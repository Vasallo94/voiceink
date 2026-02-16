import json

import settings_store


def test_load_settings_returns_defaults_for_missing_file(tmp_path):
    path = tmp_path / "missing.json"
    settings = settings_store.load_settings(str(path))
    assert settings.silence_timeout == 5
    assert settings.silence_threshold == 500
    assert settings.input_device_name is None


def test_save_and_load_settings_roundtrip(tmp_path):
    path = tmp_path / "settings.json"
    saved = settings_store.save_settings(
        settings_store.AppSettings(
            silence_timeout=5,
            silence_threshold=1200,
            input_device_name="InstaLink Mic",
        ),
        str(path),
    )

    loaded = settings_store.load_settings(str(path))

    assert saved.silence_timeout == 5
    assert saved.silence_threshold == 1200
    assert saved.input_device_name == "InstaLink Mic"
    assert loaded.silence_timeout == 5
    assert loaded.silence_threshold == 1200
    assert loaded.input_device_name == "InstaLink Mic"


def test_save_settings_clamps_values(tmp_path):
    path = tmp_path / "settings.json"
    settings_store.save_settings(
        settings_store.AppSettings(silence_timeout=100, silence_threshold=-10),
        str(path),
    )

    payload = json.loads(path.read_text())
    assert payload["silence_timeout"] == 10
    assert payload["silence_threshold"] == 200
