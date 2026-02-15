from collections import deque

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import QWidget


class WaveformWidget(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setMinimumHeight(80)
        self._values: deque[float] = deque([0.0] * 48, maxlen=48)

    def add_level(self, rms: float) -> None:
        normalized = min(max(rms / 2000.0, 0.0), 1.0)
        self._values.append(normalized)
        self.update()

    def clear_levels(self) -> None:
        self._values = deque([0.0] * 48, maxlen=48)
        self.update()

    def paintEvent(self, event) -> None:
        del event
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        width = self.width()
        height = self.height()
        count = len(self._values)
        if count == 0:
            return

        bar_w = max(width / count - 2, 2)
        x = 0.0

        for value in self._values:
            bar_h = max(height * value, 2)
            y = (height - bar_h) / 2
            color = QColor("#007AFF") if value < 0.7 else QColor("#30D158")
            painter.setBrush(color)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(x, y, bar_w, bar_h, 2, 2)
            x += bar_w + 2
