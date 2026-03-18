import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")


# Whisper (Wyoming STT)
WHISPER_HOST = os.environ.get("WHISPER_HOST", "192.168.1.42")
WHISPER_PORT = int(os.environ.get("WHISPER_PORT", "10300"))

# Home Assistant (TTS via Piper + DLNA)
HA_URL = os.environ.get("HA_URL", "http://192.168.1.42:8123")
HA_TOKEN = os.environ.get("HA_TOKEN", "")
HA_MEDIA_PLAYER = os.environ.get("HA_MEDIA_PLAYER", "media_player.kitchen_dashboard")
HA_TTS_ENTITY = os.environ.get("HA_TTS_ENTITY", "tts.piper")


# Audio capture settings (ReSpeaker via USB)
AUDIO_RATE = 16000
AUDIO_WIDTH = 2  # 16-bit
AUDIO_CHANNELS = 2  # ReSpeaker is stereo (ch1=audio, ch2=reference)
AUDIO_CHUNK = 1280  # frames per buffer

# Wake word
WAKEWORD_MODEL = os.environ.get(
    "WAKEWORD_MODEL", "/home/bbaldino/respeaker/hey_tars.onnx"
)
WAKEWORD_THRESHOLD = float(os.environ.get("WAKEWORD_THRESHOLD", "0.5"))

# Silence detection
SILENCE_RMS = int(os.environ.get("SILENCE_RMS", "500"))
SILENCE_SECS = float(os.environ.get("SILENCE_SECS", "1.5"))
