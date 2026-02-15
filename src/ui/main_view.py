from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QLabel, QPushButton, QVBoxLayout, QWidget

from .waveform_widget import WaveformWidget


class MainView(QWidget):
    record_clicked = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        self.status_label = QLabel("Listo")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.record_button = QPushButton("🎙 Grabar")
        self.record_button.setObjectName("RecordButton")
        self.record_button.clicked.connect(self.record_clicked.emit)

        self.waveform = WaveformWidget()

        self.last_title = QLabel("Última transcripción")
        self.last_title.setObjectName("Muted")
        self.last_text = QLabel("Aún no hay transcripciones")
        self.last_text.setWordWrap(True)
        self.last_text.setObjectName("Card")
        self.last_text.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.last_text.setMinimumHeight(86)
        self.last_text.setContentsMargins(10, 10, 10, 10)

        self.hotkey_hint = QLabel("Ctrl × 2 para grabar")
        self.hotkey_hint.setObjectName("Muted")
        self.hotkey_hint.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(self.status_label)
        layout.addWidget(self.record_button)
        layout.addWidget(self.waveform)
        layout.addWidget(self.last_title)
        layout.addWidget(self.last_text)
        layout.addStretch(1)
        layout.addWidget(self.hotkey_hint)

    def set_state(self, state_name: str) -> None:
        if state_name == "RECORDING":
            self.status_label.setText("Grabando...")
            self.record_button.setText("⏹ Parar")
            self.record_button.setProperty("recording", True)
        elif state_name == "PROCESSING":
            self.status_label.setText("Procesando...")
            self.record_button.setText("⏳ Procesando")
            self.record_button.setProperty("recording", False)
        else:
            self.status_label.setText("Listo")
            self.record_button.setText("🎙 Grabar")
            self.record_button.setProperty("recording", False)
            self.waveform.clear_levels()

        self.record_button.style().unpolish(self.record_button)
        self.record_button.style().polish(self.record_button)

    def set_last_transcription(self, text: str) -> None:
        value = text.strip()
        if not value:
            return

        if len(value) > 280:
            value = f"{value[:280]}..."
        self.last_text.setText(value)
