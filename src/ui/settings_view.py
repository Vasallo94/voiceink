from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QLabel, QPushButton, QSlider, QVBoxLayout, QWidget


class SettingsView(QWidget):
    settings_changed = Signal(int, int)
    request_permissions_clicked = Signal()
    retry_hotkey_clicked = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        self.timeout_label = QLabel("Silence timeout: 3s")
        self.timeout_slider = QSlider(Qt.Orientation.Horizontal)
        self.timeout_slider.setRange(1, 10)
        self.timeout_slider.setValue(3)
        self.timeout_slider.valueChanged.connect(self._on_timeout_changed)

        self.threshold_label = QLabel("Silence threshold: 800")
        self.threshold_slider = QSlider(Qt.Orientation.Horizontal)
        self.threshold_slider.setRange(200, 2000)
        self.threshold_slider.setSingleStep(50)
        self.threshold_slider.setValue(800)
        self.threshold_slider.valueChanged.connect(self._on_threshold_changed)

        self.apply_button = QPushButton("Aplicar")
        self.apply_button.clicked.connect(self._emit_settings)

        self.hotkey_status_label = QLabel("Hotkey status: checking...")
        self.permissions_button = QPushButton("Abrir permisos (opcional)")
        self.permissions_button.clicked.connect(self.request_permissions_clicked.emit)
        self.retry_hotkey_button = QPushButton("Reintentar hotkey")
        self.retry_hotkey_button.clicked.connect(self.retry_hotkey_clicked.emit)

        layout.addWidget(self.timeout_label)
        layout.addWidget(self.timeout_slider)
        layout.addWidget(self.threshold_label)
        layout.addWidget(self.threshold_slider)
        layout.addWidget(self.hotkey_status_label)
        layout.addWidget(self.permissions_button)
        layout.addWidget(self.retry_hotkey_button)
        layout.addStretch(1)
        layout.addWidget(self.apply_button)

    def _on_timeout_changed(self, value: int) -> None:
        self.timeout_label.setText(f"Silence timeout: {value}s")

    def _on_threshold_changed(self, value: int) -> None:
        self.threshold_label.setText(f"Silence threshold: {value}")

    def _emit_settings(self) -> None:
        self.settings_changed.emit(
            self.timeout_slider.value(),
            self.threshold_slider.value(),
        )

    def set_values(self, timeout_s: int, threshold: int) -> None:
        self.timeout_slider.setValue(timeout_s)
        self.threshold_slider.setValue(threshold)
        self._on_timeout_changed(timeout_s)
        self._on_threshold_changed(threshold)

    def set_hotkey_status(self, active: bool) -> None:
        label = getattr(self, "_active_hotkey_label", "Ctrl x2")
        if active:
            self.hotkey_status_label.setText(f"Hotkey status: activo ({label})")
        else:
            self.hotkey_status_label.setText(f"Hotkey status: inactivo ({label})")

    def set_hotkey_label(self, label: str) -> None:
        self._active_hotkey_label = label
