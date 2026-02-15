from PySide6.QtCore import QPoint, Qt
from PySide6.QtWidgets import QTabWidget, QVBoxLayout, QWidget

from .history_view import HistoryView
from .main_view import MainView
from .settings_view import SettingsView


class PopoverWindow(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.Popup
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.NoDropShadowWindowHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        self.setFixedSize(340, 500)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)

        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)

        self.main_view = MainView()
        self.history_view = HistoryView()
        self.settings_view = SettingsView()

        self.tabs.addTab(self.main_view, "Principal")
        self.tabs.addTab(self.history_view, "Historial")
        self.tabs.addTab(self.settings_view, "Ajustes")

        layout.addWidget(self.tabs)

    def toggle_near(self, origin: QPoint) -> None:
        if self.isVisible():
            self.hide()
            return

        self.move(origin)
        self.show()
        self.raise_()
        self.activateWindow()

    def set_state(self, state_name: str) -> None:
        self.main_view.set_state(state_name)

    def set_last_transcription(self, text: str) -> None:
        self.main_view.set_last_transcription(text)

    def set_history(self, entries: list[dict]) -> None:
        self.history_view.load_entries(entries)
