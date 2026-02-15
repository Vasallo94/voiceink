from datetime import datetime

import pyperclip
import sounds
from PySide6.QtWidgets import QListWidget, QListWidgetItem, QVBoxLayout, QWidget


class HistoryView(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(8)

        self.list_widget = QListWidget()
        self.list_widget.itemClicked.connect(self._on_item_clicked)
        layout.addWidget(self.list_widget)

    def load_entries(self, entries: list[dict]) -> None:
        self.list_widget.clear()
        if not entries:
            self.list_widget.addItem(QListWidgetItem("(empty)"))
            return

        for entry in reversed(entries):
            text = entry.get("text", "")
            timestamp = self._format_timestamp(entry.get("timestamp", ""))
            preview = f"{text[:90]}..." if len(text) > 90 else text

            item = QListWidgetItem(f"[{timestamp}] {preview}")
            item.setData(0x0100, text)
            self.list_widget.addItem(item)

    def _on_item_clicked(self, item: QListWidgetItem) -> None:
        text = item.data(0x0100)
        if not text:
            return

        pyperclip.copy(text)
        sounds.play_success()

    def _format_timestamp(self, value: str) -> str:
        if not value:
            return "-"

        try:
            dt = datetime.fromisoformat(value)
            return dt.strftime("%d/%m %H:%M")
        except ValueError:
            return value[:16].replace("T", " ")
