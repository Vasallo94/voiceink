"""Sound feedback utilities for Voice2Clip using macOS system sounds."""

import logging
import subprocess

logger = logging.getLogger(__name__)

# macOS system sounds (available without extra dependencies)
SOUND_START = "/System/Library/Sounds/Tink.aiff"
SOUND_STOP = "/System/Library/Sounds/Pop.aiff"
SOUND_ERROR = "/System/Library/Sounds/Basso.aiff"


def play(sound_path: str) -> None:
    """Play a system sound asynchronously using afplay (macOS)."""
    try:
        subprocess.Popen(
            ["afplay", sound_path],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except FileNotFoundError:
        logger.debug("afplay not available (not macOS?)")
    except Exception as e:
        logger.debug("Could not play sound: %s", e)


def play_start() -> None:
    """Play the recording-started sound."""
    play(SOUND_START)


def play_stop() -> None:
    """Play the recording-stopped sound."""
    play(SOUND_STOP)


def play_error() -> None:
    """Play the error sound."""
    play(SOUND_ERROR)


def play_success() -> None:
    """Play the success sound (transcription ready)."""
    # 'Hero' or 'Glass' are good standard sounds
    play("/System/Library/Sounds/Hero.aiff")
