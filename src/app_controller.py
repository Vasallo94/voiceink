import logging
import os
import threading
import time
from enum import Enum, auto

import history
import pyperclip
import settings_store
import sounds
from hotkey_handler import HotkeyHandler
from PySide6.QtCore import QObject, Signal
from recorder import AudioRecorder
from transcriber import GeminiTranscriber

logger = logging.getLogger(__name__)

AUDIO_RETENTION_MODE = os.getenv("VOICE2CLIP_AUDIO_RETENTION", "delete").strip().lower()


class AppState(Enum):
    IDLE = auto()
    RECORDING = auto()
    PROCESSING = auto()


class AppController(QObject):
    state_changed = Signal(str)
    audio_level = Signal(float)
    transcription_ready = Signal(str)
    history_updated = Signal()
    notification_requested = Signal(str, str, str)
    error_occurred = Signal(str)

    _hotkey_triggered = Signal()
    _silence_detected = Signal()

    def __init__(self) -> None:
        super().__init__()
        recording_target = os.path.expanduser("~/.voice2clip_recording.wav")
        persist_mode = os.getenv("VOICE2CLIP_PERSIST_MODE", "normal").strip().lower()
        if persist_mode == "memory":
            recording_target = "/tmp/voice2clip_recording.wav"

        self.recorder = AudioRecorder(
            filename=recording_target,
            silence_threshold=800,
            silence_timeout=3,
        )
        self.settings = settings_store.load_settings()
        self.recorder.silence_timeout = self.settings.silence_timeout
        self.recorder.silence_threshold = self.settings.silence_threshold

        self.transcriber: GeminiTranscriber | None
        try:
            self.transcriber = GeminiTranscriber()
        except ValueError as e:
            self.transcriber = None
            self.error_occurred.emit(str(e))

        self.hotkey_handler = HotkeyHandler(callback=self.on_hotkey, double_press_window=0.35)

        self._recording_start_time: float = 0.0
        self._state = AppState.IDLE
        self._state_lock = threading.Lock()

        self._hotkey_triggered.connect(self._toggle_from_hotkey)
        self._silence_detected.connect(self._stop_and_process_from_silence)

    def start(self) -> None:
        started = self.hotkey_handler.start()
        if started is False:
            self.notification_requested.emit(
                "Voice2Clip",
                "Hotkey unavailable",
                "No se pudo iniciar hotkey global.",
            )
        elif self.hotkey_handler.is_using_carbon():
            self.notification_requested.emit(
                "Voice2Clip",
                "Hotkey activo",
                f"Usando {self.hotkey_handler.active_hotkey_label}",
            )

    def ensure_hotkey_started(self) -> bool:
        return self.hotkey_handler.ensure_started()

    def get_active_hotkey_label(self) -> str:
        return self.hotkey_handler.active_hotkey_label

    def is_hotkey_active(self) -> bool:
        return self.hotkey_handler.is_operational()

    def shutdown(self) -> None:
        self.hotkey_handler.stop()
        self.recorder.cleanup()

    def get_recent_history(self, count: int = 10) -> list[dict]:
        return history.get_recent(count)

    def get_settings(self) -> settings_store.AppSettings:
        return self.settings

    def set_silence_timeout(self, value: int) -> None:
        self.recorder.silence_timeout = value
        self.settings = settings_store.save_settings(
            settings_store.AppSettings(
                silence_timeout=self.recorder.silence_timeout,
                silence_threshold=self.recorder.silence_threshold,
            )
        )
        self.recorder.silence_timeout = self.settings.silence_timeout
        self.recorder.silence_threshold = self.settings.silence_threshold

    def set_silence_threshold(self, value: int) -> None:
        self.recorder.silence_threshold = value
        self.settings = settings_store.save_settings(
            settings_store.AppSettings(
                silence_timeout=self.recorder.silence_timeout,
                silence_threshold=self.recorder.silence_threshold,
            )
        )
        self.recorder.silence_timeout = self.settings.silence_timeout
        self.recorder.silence_threshold = self.settings.silence_threshold

    def is_hotkey_trusted(self) -> bool:
        return self.hotkey_handler.is_operational()

    def request_accessibility_permission(self) -> bool:
        return self.hotkey_handler.request_accessibility_permission()

    def on_hotkey(self) -> None:
        self._hotkey_triggered.emit()

    def _toggle_from_hotkey(self) -> None:
        self.toggle_recording(trigger_source="hotkey")

    def _stop_and_process_from_silence(self) -> None:
        self._stop_and_process(stop_source="silence")

    def _get_state(self) -> AppState:
        with self._state_lock:
            return self._state

    def _transition_state(self, expected: AppState, new_state: AppState) -> bool:
        with self._state_lock:
            if self._state != expected:
                return False
            self._state = new_state
            return True

    def _set_state(self, new_state: AppState) -> None:
        with self._state_lock:
            self._state = new_state

    def toggle_recording(self, trigger_source: str | None = None) -> None:
        source = trigger_source or "ui"
        state = self._get_state()
        logger.info("Toggle requested (source=%s, state=%s)", source, state.name)

        if state == AppState.PROCESSING:
            return

        if state == AppState.IDLE:
            self._start_recording(start_source=source)
            return

        self._stop_and_process(stop_source=source)

    def _start_recording(self, start_source: str = "unknown") -> None:
        if not self._transition_state(AppState.IDLE, AppState.RECORDING):
            return

        logger.info("Recording started (source=%s)", start_source)
        self.state_changed.emit(AppState.RECORDING.name)
        self._recording_start_time = time.time()

        sounds.play_start()
        self.notification_requested.emit(
            "Voice2Clip",
            "Listening...",
            "Speak now. Silence or Shortcut to stop.",
        )

        try:
            self.recorder.start(
                stop_callback=self._on_silence_detected,
                level_callback=self._on_audio_level,
            )
        except Exception as e:
            self._set_state(AppState.IDLE)
            self.state_changed.emit(AppState.IDLE.name)
            sounds.play_error()
            self.error_occurred.emit(str(e))

    def _on_audio_level(self, rms: float) -> None:
        self.audio_level.emit(rms)

    def _on_silence_detected(self) -> None:
        self._silence_detected.emit()

    def _stop_and_process(self, stop_source: str = "unknown") -> None:
        if not self._transition_state(AppState.RECORDING, AppState.PROCESSING):
            return

        logger.info("Stopping and processing (source=%s)", stop_source)
        self.state_changed.emit(AppState.PROCESSING.name)

        duration = time.time() - self._recording_start_time
        file_path = self.recorder.stop()
        sounds.play_stop()

        threading.Thread(
            target=self._process_audio, args=(file_path, duration), daemon=True
        ).start()

    def _process_audio(self, file_path: str, duration: float) -> None:
        if not self.transcriber:
            sounds.play_error()
            self.error_occurred.emit("API Key Missing")
            self._finish_idle()
            self._maybe_cleanup_audio(file_path)
            return

        result = self.transcriber.transcribe(file_path)
        ignore_phrases = ["no hay audio", "no audio", "sin audio", "silencio detectado"]
        is_bad_response = any(phrase in result.lower() for phrase in ignore_phrases)

        if result.startswith("Error") or is_bad_response:
            sounds.play_error()
            self.notification_requested.emit("Voice2Clip", "Ignored", result[:80])
            self._finish_idle()
            self._maybe_cleanup_audio(file_path)
            return

        history.save_entry(result, duration_secs=duration)
        pyperclip.copy(result)
        self.transcription_ready.emit(result)
        self.history_updated.emit()

        sounds.play_success()
        self.notification_requested.emit(
            "Voice2Clip",
            "Copied to Clipboard!",
            result[:100],
        )

        self._finish_idle()
        self._maybe_cleanup_audio(file_path)

    def _finish_idle(self) -> None:
        self._set_state(AppState.IDLE)
        self.state_changed.emit(AppState.IDLE.name)

    def _maybe_cleanup_audio(self, file_path: str) -> None:
        if AUDIO_RETENTION_MODE in {"keep", "ttl"}:
            return

        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except OSError as e:
            logger.debug("Could not delete temp audio file: %s", e)
