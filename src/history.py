"""Transcription history manager — stores recent transcriptions to a local JSON file."""

import json
import logging
import os
from datetime import datetime

logger = logging.getLogger(__name__)

DEFAULT_HISTORY_PATH = os.path.expanduser("~/.voice2clip_history.json")


def _env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        logger.warning("Invalid %s=%r, using default %d", name, value, default)
        return default


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


MAX_HISTORY_ITEMS = _env_int("VOICE2CLIP_HISTORY_MAX_ITEMS", 50)
HISTORY_RETENTION_DAYS = _env_int("VOICE2CLIP_HISTORY_RETENTION_DAYS", 0)
HISTORY_ENABLED = _env_bool("VOICE2CLIP_HISTORY_ENABLED", True)


def get_file_version(path: str = DEFAULT_HISTORY_PATH) -> tuple[int, int]:
    """Return a lightweight file version tuple (mtime_ns, size)."""
    if not os.path.exists(path):
        return (0, 0)
    try:
        stat = os.stat(path)
        return (stat.st_mtime_ns, stat.st_size)
    except OSError:
        return (0, 0)


def _prune_history(items: list[dict]) -> list[dict]:
    if HISTORY_RETENTION_DAYS > 0:
        now = datetime.now()
        kept: list[dict] = []
        for item in items:
            timestamp = item.get("timestamp")
            if not isinstance(timestamp, str):
                continue
            try:
                dt = datetime.fromisoformat(timestamp)
            except ValueError:
                continue
            age_days = (now - dt).days
            if age_days <= HISTORY_RETENTION_DAYS:
                kept.append(item)
        items = kept

    if len(items) > MAX_HISTORY_ITEMS:
        items = items[-MAX_HISTORY_ITEMS:]

    return items


def load_history(path: str = DEFAULT_HISTORY_PATH) -> list[dict]:
    """Load transcription history from disk."""
    if not HISTORY_ENABLED:
        return []

    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            loaded = json.load(f)
        if not isinstance(loaded, list):
            return []
        return _prune_history(loaded)
    except (json.JSONDecodeError, IOError) as e:
        logger.warning("Could not load history: %s", e)
        return []


def save_entry(text: str, duration_secs: float = 0, path: str = DEFAULT_HISTORY_PATH) -> None:
    """Append a transcription entry to history."""
    if not HISTORY_ENABLED:
        return

    history = load_history(path)
    entry = {
        "timestamp": datetime.now().isoformat(),
        "text": text,
        "duration_secs": round(duration_secs, 1),
    }
    history.append(entry)
    history = _prune_history(history)

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
