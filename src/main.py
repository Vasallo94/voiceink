import logging
import os
import subprocess
import sys

from app_controller import AppController
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication
from ui.popover_window import PopoverWindow
from ui.theme import apply_theme
from ui.tray_manager import TrayManager

log_file = os.path.expanduser("~/.voice2clip.log")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    datefmt="%H:%M:%S",
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


class Voice2ClipApp:
    def __init__(self) -> None:
        self.qt_app = QApplication(sys.argv)
        self.qt_app.setQuitOnLastWindowClosed(False)

        apply_theme(self.qt_app)

        self.controller = AppController()
        self.popover = PopoverWindow()
        self.tray = TrayManager(
            popover=self.popover,
            on_toggle=self._on_toggle,
            on_quit=self.quit,
        )

        self._history_timer = QTimer()
        self._history_timer.setInterval(2000)
        self._history_timer.timeout.connect(self._refresh_history)

        self._hotkey_timer = QTimer()
        self._hotkey_timer.setInterval(2500)
        self._hotkey_timer.timeout.connect(self._ensure_hotkey)

        self._success_timer = QTimer()
        self._success_timer.setSingleShot(True)
        self._success_timer.setInterval(1200)
        self._success_timer.timeout.connect(lambda: self.tray.set_state_icon("IDLE"))

        self._connect_signals()
        self._load_initial_settings()
        self._refresh_history()

    def _connect_signals(self) -> None:
        self.controller.state_changed.connect(self._on_state_changed)
        self.controller.audio_level.connect(self.popover.main_view.waveform.add_level)
        self.controller.transcription_ready.connect(self._on_transcription_ready)
        self.controller.history_updated.connect(self._refresh_history)
        self.controller.notification_requested.connect(self.tray.show_message)
        self.controller.error_occurred.connect(self._on_error)

        self.popover.main_view.record_clicked.connect(self._on_toggle)
        self.popover.settings_view.settings_changed.connect(self._on_settings_changed)
        self.popover.settings_view.request_permissions_clicked.connect(
            self._open_accessibility_settings
        )
        self.popover.settings_view.retry_hotkey_clicked.connect(self._retry_hotkey)

    def _on_toggle(self) -> None:
        self.controller.toggle_recording(trigger_source="ui")

    def _on_state_changed(self, state_name: str) -> None:
        self.popover.set_state(state_name)
        self.tray.set_state_icon(state_name)

    def _on_transcription_ready(self, text: str) -> None:
        self.popover.set_last_transcription(text)
        self.tray.show_success_flash()
        self._success_timer.start()

    def _on_error(self, message: str) -> None:
        logger.error("Controller error: %s", message)
        self.tray.show_message("Voice2Clip", "Error", message)

    def _refresh_history(self) -> None:
        self.popover.set_history(self.controller.get_recent_history(10))

    def _load_initial_settings(self) -> None:
        settings = self.controller.get_settings()
        self.popover.settings_view.set_values(
            settings.silence_timeout,
            settings.silence_threshold,
        )
        self.popover.settings_view.set_hotkey_label(self.controller.get_active_hotkey_label())
        self.popover.settings_view.set_hotkey_status(self.controller.is_hotkey_trusted())

    def _on_settings_changed(self, timeout_s: int, threshold: int) -> None:
        self.controller.set_silence_timeout(timeout_s)
        self.controller.set_silence_threshold(threshold)
        current = self.controller.get_settings()
        self.popover.settings_view.set_values(current.silence_timeout, current.silence_threshold)
        self.tray.show_message("Voice2Clip", "Settings", "Audio settings updated")

    def _open_accessibility_settings(self) -> None:
        self.controller.request_accessibility_permission()
        subprocess.Popen(
            [
                "open",
                "x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility",
            ]
        )

    def _retry_hotkey(self) -> None:
        started = self.controller.ensure_hotkey_started()
        self.popover.settings_view.set_hotkey_label(self.controller.get_active_hotkey_label())
        self.popover.settings_view.set_hotkey_status(self.controller.is_hotkey_trusted())
        if started:
            self.tray.show_message(
                "Voice2Clip",
                "Hotkey",
                f"Hotkey activo: {self.controller.get_active_hotkey_label()}",
            )
            self._hotkey_timer.stop()
        else:
            self.tray.show_message("Voice2Clip", "Hotkey", "Sigue sin permisos")

    def run(self) -> int:
        self.controller.start()
        self._history_timer.start()
        self._hotkey_timer.start()
        return self.qt_app.exec()

    def _ensure_hotkey(self) -> None:
        trusted = self.controller.is_hotkey_trusted()
        self.popover.settings_view.set_hotkey_label(self.controller.get_active_hotkey_label())
        self.popover.settings_view.set_hotkey_status(trusted)
        if self.controller.ensure_hotkey_started():
            self._hotkey_timer.stop()

    def quit(self) -> None:
        logger.info("Shutting down...")
        self._history_timer.stop()
        self._hotkey_timer.stop()
        self._success_timer.stop()
        self.controller.shutdown()
        self.qt_app.quit()


if __name__ == "__main__":
    app = Voice2ClipApp()
    raise SystemExit(app.run())
