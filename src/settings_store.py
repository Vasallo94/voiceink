import json
import logging
import os
from dataclasses import asdict, dataclass

logger = logging.getLogger(__name__)

DEFAULT_SETTINGS_PATH = os.path.expanduser("~/.voice2clip_settings.json")


@dataclass(slots=True)
class AppSettings:
    silence_timeout: int = 5
    silence_threshold: int = 500
    input_device_name: str | None = None


def _clamp_timeout(value: int) -> int:
    return max(1, min(10, value))


def _clamp_threshold(value: int) -> int:
    return max(200, min(2000, value))


def sanitize(settings: AppSettings) -> AppSettings:
    cleaned_device_name = settings.input_device_name
    if isinstance(cleaned_device_name, str):
        cleaned_device_name = cleaned_device_name.strip() or None
    elif cleaned_device_name is not None:
        cleaned_device_name = None

    return AppSettings(
        silence_timeout=_clamp_timeout(settings.silence_timeout),
        silence_threshold=_clamp_threshold(settings.silence_threshold),
        input_device_name=cleaned_device_name,
    )


def load_settings(path: str = DEFAULT_SETTINGS_PATH) -> AppSettings:
    if not os.path.exists(path):
        return AppSettings()

    try:
        with open(path, "r", encoding="utf-8") as file:
            payload = json.load(file)
    except (OSError, json.JSONDecodeError) as error:
        logger.warning("Could not load settings: %s", error)
        return AppSettings()

    if not isinstance(payload, dict):
        return AppSettings()

    timeout = payload.get("silence_timeout", 5)
    threshold = payload.get("silence_threshold", 500)
    input_device_name = payload.get("input_device_name")

    try:
        settings = AppSettings(
            silence_timeout=int(timeout),
            silence_threshold=int(threshold),
            input_device_name=input_device_name,
        )
    except (TypeError, ValueError):
        return AppSettings()

    return sanitize(settings)


def save_settings(settings: AppSettings, path: str = DEFAULT_SETTINGS_PATH) -> AppSettings:
    sanitized = sanitize(settings)

    try:
        with open(path, "w", encoding="utf-8") as file:
            json.dump(asdict(sanitized), file, ensure_ascii=False, indent=2)
    except OSError as error:
        logger.error("Could not save settings: %s", error)

    return sanitized
