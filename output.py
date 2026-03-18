"""Send TTS audio to tablet for playback via Home Assistant + Piper + DLNA."""

import logging

import aiohttp

import config

logger = logging.getLogger(__name__)


async def speak(text: str) -> None:
    """Send TTS text to Home Assistant, which synthesizes with Piper and plays via DLNA."""
    url = f"{config.HA_URL}/api/services/tts/speak"
    headers = {
        "Authorization": f"Bearer {config.HA_TOKEN}",
        "Content-Type": "application/json",
    }
    payload = {
        "entity_id": config.HA_TTS_ENTITY,
        "media_player_entity_id": config.HA_MEDIA_PLAYER,
        "message": text,
    }
    logger.info("TTS via HA: %s", text[:80])
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload, headers=headers) as resp:
            body = await resp.text()
            logger.info("HA response: %s %s", resp.status, body[:200])
