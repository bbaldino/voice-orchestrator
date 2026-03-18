# Voice Orchestrator

Voice pipeline that runs on a Raspberry Pi Zero 2 W with a ReSpeaker XVF3800 USB mic array. Listens for a wake word, transcribes speech, generates a response, and plays it back on a tablet via Home Assistant + Piper TTS.

## Pipeline

1. **Wake word detection** — openwakeword (ONNX) listens continuously on the ReSpeaker
2. **Recording** — captures audio until silence is detected
3. **STT** — sends audio to Whisper via Wyoming protocol
4. **Response** — generates response text (placeholder, will be replaced with LLM)
5. **TTS** — sends text to Home Assistant, which synthesizes with Piper and plays on a tablet via DLNA (BubbleUPnP)

The ReSpeaker LED ring provides visual feedback: blue on wake word detection, breathing blue while processing, off when idle.

## Setup

### Prerequisites

- Raspberry Pi Zero 2 W (or similar) with ReSpeaker XVF3800 USB mic array
- Whisper (faster-whisper) running as a Wyoming server
- Piper TTS integrated with Home Assistant
- Tablet with BubbleUPnP (DLNA renderer) for audio output
- `xvf_host` binary for LED control (from [reSpeaker_XVF3800_USB_4MIC_ARRAY](https://github.com/respeaker/reSpeaker_XVF3800_USB_4MIC_ARRAY))

### Install

```bash
python -m venv venv
source venv/bin/activate
bash install.sh
```

### Configure

All settings are in `config.py` and can be overridden via environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `WHISPER_HOST` | `192.168.1.42` | Whisper Wyoming server host |
| `WHISPER_PORT` | `10300` | Whisper Wyoming server port |
| `HA_URL` | `http://192.168.1.42:8123` | Home Assistant URL |
| `HA_TOKEN` | *(required)* | Home Assistant long-lived access token |
| `HA_MEDIA_PLAYER` | `media_player.kitchen_dashboard` | HA media player entity for audio output |
| `HA_TTS_ENTITY` | `tts.piper` | HA TTS entity |
| `WAKEWORD_MODEL` | `/home/bbaldino/respeaker/hey_tars.onnx` | Path to openwakeword model |
| `WAKEWORD_THRESHOLD` | `0.5` | Wake word confidence threshold |
| `SILENCE_RMS` | `500` | RMS threshold for silence detection |
| `SILENCE_SECS` | `1.5` | Seconds of silence before stopping recording |

### Run as a service

```bash
sudo cp voice-orchestrator.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable voice-orchestrator
sudo systemctl start voice-orchestrator
```

Logs: `journalctl -u voice-orchestrator -f`

### LED control

The ReSpeaker XVF3800 LEDs require USB device permissions. Add a udev rule to avoid needing sudo:

```bash
echo 'SUBSYSTEM=="usb", ATTR{idVendor}=="2886", ATTR{idProduct}=="0018", MODE="0666"' | sudo tee /etc/udev/rules.d/99-respeaker.rules
sudo udevadm control --reload-rules && sudo udevadm trigger
```

Verify the vendor/product IDs with `lsusb` first.
