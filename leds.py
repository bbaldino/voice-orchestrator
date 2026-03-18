"""Control ReSpeaker XVF3800 LED ring via xvf_host."""

import logging
import subprocess

logger = logging.getLogger(__name__)

XVF_HOST = "/home/bbaldino/xvf3800/xvf_host"


def _run(cmd: str, *args: str) -> None:
    try:
        subprocess.run(
            ["sudo", XVF_HOST, cmd, *args],
            capture_output=True,
            timeout=5,
        )
    except Exception as e:
        logger.warning("LED command failed: %s", e)


def wake() -> None:
    """Wake word detected — half-brightness blue."""
    _run("led_color", "0x004488")
    _run("led_brightness", "128")
    _run("led_effect", "3")


def thinking() -> None:
    """Processing — breathing blue."""
    _run("led_color", "0x0088ff")
    _run("led_brightness", "255")
    _run("led_effect", "1")


def speaking() -> None:
    """Response playing — solid cyan."""
    _run("led_color", "0x00ffff")
    _run("led_effect", "3")


def idle() -> None:
    """Listening for wake word — LEDs off."""
    _run("led_effect", "0")
