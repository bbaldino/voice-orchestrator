"""
Voice pipeline orchestrator.

Captures audio from ReSpeaker via USB, detects wake word with openwakeword,
records until silence, then fans out to STT + speaker recognition in parallel.
Sends response audio to the Fully Kiosk tablet.
"""

import asyncio
import io
import logging
import wave

import numpy as np
import pyaudio
from aiohttp import web
from openwakeword.model import Model

import config
from stt import transcribe
from output import speak, get_voice, set_voice
import leds

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)


def to_mono(data: bytes) -> bytes:
    """Convert interleaved stereo int16 audio to mono (first channel)."""
    samples = np.frombuffer(data, dtype=np.int16)
    return samples[0 :: config.AUDIO_CHANNELS].tobytes()


def find_respeaker(p: pyaudio.PyAudio) -> int:
    """Find the ReSpeaker USB audio device index."""
    for i in range(p.get_device_count()):
        info = p.get_device_info_by_index(i)
        if (
            "respeaker" in info["name"].lower()
            and info["maxInputChannels"] >= config.AUDIO_CHANNELS
        ):
            logger.info("Using device %d: %s", i, info["name"])
            return i
    raise RuntimeError("ReSpeaker device not found")


def record_until_silence(stream) -> bytes:
    """Record audio until silence is detected, return mono PCM bytes."""
    frames = []
    silent_chunks = 0
    max_silent = int(config.SILENCE_SECS * config.AUDIO_RATE / config.AUDIO_CHUNK)

    while True:
        data = stream.read(config.AUDIO_CHUNK, exception_on_overflow=False)
        mono = to_mono(data)
        frames.append(mono)
        rms = np.sqrt(
            np.mean(np.frombuffer(mono, dtype=np.int16).astype(np.float32) ** 2)
        )
        silent_chunks = silent_chunks + 1 if rms < config.SILENCE_RMS else 0
        if silent_chunks >= max_silent:
            return b"".join(frames)


def wrap_as_wav(raw_audio: bytes) -> bytes:
    """Wrap raw mono PCM bytes in a WAV header."""
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(config.AUDIO_WIDTH)
        wf.setframerate(config.AUDIO_RATE)
        wf.writeframes(raw_audio)
    return buf.getvalue()


def get_response(text: str, speaker: str) -> str:
    """Placeholder brain — replace with actual LLM/intent handling."""
    prefix = f"Hey {speaker}, " if speaker != "unknown" else ""
    lower = text.lower()
    if "timer" in lower:
        return f"{prefix}Sure, setting a timer."
    if "weather" in lower:
        return f"{prefix}It looks sunny today."
    if "time" in lower:
        return f"{prefix}I'm not sure what time it is."
    if "calendar" in lower:
        return (
            f"{prefix}You've got 3 appointments tomorrow. "
            "At 10am you have a meeting. At noon you've got lunch with Larry David. "
            "In the evening you're going out to dinner with Amanda."
        )
    return f"{prefix}I heard you say: {text}"


async def process_utterance(audio: bytes) -> None:
    """Run STT, then respond."""
    # Save clip for debugging
    debug_wav = wrap_as_wav(audio)
    with open("/tmp/last_utterance.wav", "wb") as f:
        f.write(debug_wav)
    logger.info("Saved debug clip to /tmp/last_utterance.wav")

    transcript = await transcribe(audio)
    speaker = "unknown"

    logger.info("Said: %s", transcript)

    if not transcript:
        return

    response = get_response(transcript, speaker)
    logger.info("Response: %s", response)

    try:
        await speak(response)
    except Exception as e:
        logger.warning("Tablet TTS failed: %s", e)


async def handle_get_voice(request):
    return web.json_response({"voice": get_voice()})


async def handle_set_voice(request):
    data = await request.json()
    voice = data.get("voice", "")
    set_voice(voice)
    return web.json_response({"voice": voice})


async def start_api_server():
    """Run a small HTTP server for receiving configuration updates."""
    app = web.Application()
    app.router.add_get("/voice", handle_get_voice)
    app.router.add_post("/voice", handle_set_voice)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, config.API_HOST, config.API_PORT)
    await site.start()
    logger.info("API server listening on %s:%d", config.API_HOST, config.API_PORT)
    return runner


async def main() -> None:
    # Start API server
    api_runner = await start_api_server()

    # Load wake word model
    oww = Model(
        wakeword_models=[config.WAKEWORD_MODEL],
        inference_framework="onnx",
    )
    logger.info("Loaded wakeword models: %s", list(oww.models.keys()))

    # Open ReSpeaker mic
    p = pyaudio.PyAudio()
    mic_index = find_respeaker(p)
    stream = p.open(
        format=pyaudio.paInt16,
        channels=config.AUDIO_CHANNELS,
        rate=config.AUDIO_RATE,
        input=True,
        input_device_index=mic_index,
        frames_per_buffer=config.AUDIO_CHUNK,
    )

    logger.info("Listening for wake word...")
    loop = asyncio.get_event_loop()
    try:
        while True:
            raw = await loop.run_in_executor(
                None, stream.read, config.AUDIO_CHUNK, False,
            )
            mono = np.frombuffer(to_mono(raw), dtype=np.int16)
            oww.predict(mono)
            scores = {
                k: max(v)
                for k, v in oww.prediction_buffer.items()
                if max(v) > config.WAKEWORD_THRESHOLD
            }
            if scores:
                logger.info("Wake word detected! %s", scores)
                leds.wake()
                logger.info("Recording...")
                clip = record_until_silence(stream)
                logger.info("Captured %d bytes, processing...", len(clip))
                leds.thinking()
                await process_utterance(clip)
                leds.idle()
                oww.reset()
                logger.info("Listening for wake word...")
    except KeyboardInterrupt:
        logger.info("Shutting down")
    finally:
        stream.stop_stream()
        stream.close()
        p.terminate()
        await api_runner.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
