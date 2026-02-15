"""Integration-style tests for AppController flow with mocked side effects."""

from unittest.mock import Mock

import app_controller
from app_controller import AppController, AppState


class ImmediateThread:
    def __init__(self, target=None, args=(), daemon=None):
        self._target = target
        self._args = args

    def start(self):
        if self._target:
            self._target(*self._args)


class DummyRecorder:
    def __init__(self, *args, **kwargs):
        self.start = Mock()
        self.stop = Mock(return_value="/tmp/voice2clip_test.wav")
        self.cleanup = Mock()
        self.silence_timeout = 3
        self.silence_threshold = 800


class DummyTranscriber:
    def __init__(self, *args, **kwargs):
        self.transcribe = Mock(return_value="texto limpio")


class DummyHotkeyHandler:
    def __init__(self, callback, double_press_window):
        self.callback = callback

    def start(self):
        return None

    def stop(self):
        return None

    def is_accessibility_trusted(self):
        return True


def make_controller(monkeypatch):
    monkeypatch.setattr(app_controller, "AudioRecorder", DummyRecorder)
    monkeypatch.setattr(app_controller, "GeminiTranscriber", DummyTranscriber)
    monkeypatch.setattr(app_controller, "HotkeyHandler", DummyHotkeyHandler)
    monkeypatch.setattr(app_controller.threading, "Thread", ImmediateThread)

    monkeypatch.setattr(app_controller.history, "save_entry", Mock())
    monkeypatch.setattr(app_controller.pyperclip, "copy", Mock())
    monkeypatch.setattr(app_controller.sounds, "play_start", Mock())
    monkeypatch.setattr(app_controller.sounds, "play_stop", Mock())
    monkeypatch.setattr(app_controller.sounds, "play_success", Mock())
    monkeypatch.setattr(app_controller.sounds, "play_error", Mock())

    return AppController()


class TestMainIntegrationFlow:
    def test_hotkey_from_idle_starts_recording(self, monkeypatch):
        app = make_controller(monkeypatch)

        app.on_hotkey()

        app.recorder.start.assert_called_once()
        assert app._get_state() == AppState.RECORDING
        app_controller.sounds.play_start.assert_called_once()

    def test_hotkey_twice_runs_success_flow_to_clipboard(self, monkeypatch):
        app = make_controller(monkeypatch)

        app.on_hotkey()
        app.on_hotkey()

        assert app.recorder.start.call_count == 1
        assert app.recorder.stop.call_count == 1
        app_controller.sounds.play_stop.assert_called_once()
        app_controller.history.save_entry.assert_called_once()
        app_controller.pyperclip.copy.assert_called_once_with("texto limpio")
        app_controller.sounds.play_success.assert_called_once()
        assert app._get_state() == AppState.IDLE

    def test_error_result_does_not_copy_clipboard(self, monkeypatch):
        app = make_controller(monkeypatch)
        assert app.transcriber is not None
        app.transcriber.transcribe.return_value = "Error during transcription: API down"

        app.toggle_recording()
        app.toggle_recording()

        app_controller.pyperclip.copy.assert_not_called()
        app_controller.history.save_entry.assert_not_called()
        app_controller.sounds.play_error.assert_called_once()
        assert app._get_state() == AppState.IDLE

    def test_processing_state_ignores_hotkey(self, monkeypatch):
        app = make_controller(monkeypatch)
        app._set_state(AppState.PROCESSING)

        app.on_hotkey()

        app.recorder.start.assert_not_called()
        app.recorder.stop.assert_not_called()
        app_controller.pyperclip.copy.assert_not_called()
        assert app._get_state() == AppState.PROCESSING
