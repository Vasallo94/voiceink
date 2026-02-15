"""Transcription history manager — stores recent transcriptions to a local JSON file."""

import json
import logging
import os
from datetime import datetime

logger = logging.getLogger(__name__)

DEFAULT_HISTORY_PATH = os.path.expanduser("~/.voice2clip_history.json")
MAX_HISTORY_ITEMS = 50


def load_history(path: str = DEFAULT_HISTORY_PATH) -> list[dict]:
    """Load transcription history from disk."""
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        logger.warning("Could not load history: %s", e)
        return []


def save_entry(text: str, duration_secs: float = 0, path: str = DEFAULT_HISTORY_PATH) -> None:
    """Append a transcription entry to history."""
    history = load_history(path)
    entry = {
        "timestamp": datetime.now().isoformat(),
        "text": text,
        "duration_secs": round(duration_secs, 1),
    }
    history.append(entry)

    # Keep only the last N entries
    if len(history) > MAX_HISTORY_ITEMS:
        history = history[-MAX_HISTORY_ITEMS:]

    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
        logger.debug("History saved (%d entries)", len(history))
    except IOError as e:
        logger.error("Could not save history: %s", e)


def get_recent(n: int = 10, path: str = DEFAULT_HISTORY_PATH) -> list[dict]:
    """Get the last N transcription entries."""
    history = load_history(path)
    return history[-n:]
