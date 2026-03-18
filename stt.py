"""Send audio to Whisper via Wyoming protocol, get transcript back."""

import logging

from wyoming.asr import Transcript
from wyoming.audio import AudioChunk, AudioStart, AudioStop
from wyoming.client import AsyncTcpClient

from config import AUDIO_RATE, AUDIO_WIDTH, WHISPER_HOST, WHISPER_PORT

logger = logging.getLogger(__name__)


async def transcribe(audio: bytes) -> str:
    """Send audio bytes to Whisper, return transcript text."""
    logger.info("Sending %d bytes to Whisper", len(audio))
    async with AsyncTcpClient(WHISPER_HOST, WHISPER_PORT) as client:
        await client.write_event(
            AudioStart(rate=AUDIO_RATE, width=AUDIO_WIDTH, channels=1).event()
        )
        # Send in 1024-byte chunks
        for i in range(0, len(audio), 1024):
            await client.write_event(
                AudioChunk(
                    rate=AUDIO_RATE,
                    width=AUDIO_WIDTH,
                    channels=1,
                    audio=audio[i : i + 1024],
                ).event()
            )
        await client.write_event(AudioStop().event())

        while True:
            event = await client.read_event()
            if event is None:
                return ""
            if Transcript.is_type(event.type):
                text = Transcript.from_event(event).text
                logger.info("Transcript: %s", text)
                return text
