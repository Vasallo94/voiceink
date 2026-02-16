from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QComboBox, QLabel, QPushButton, QSlider, QVBoxLayout, QWidget


class SettingsView(QWidget):
    settings_changed = Signal(int, int, str)
    request_permissions_clicked = Signal()
    retry_hotkey_clicked = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(12)

        audio_card = QWidget()
        audio_card.setObjectName("Card")
        audio_layout = QVBoxLayout(audio_card)
        audio_layout.setContentsMargins(12, 12, 12, 12)
        audio_layout.setSpacing(8)

        audio_title = QLabel("Audio")
        audio_title.setObjectName("Muted")
        audio_layout.addWidget(audio_title)

        self.timeout_label = QLabel("Tiempo de silencio: 5s")
        self.timeout_slider = QSlider(Qt.Orientation.Horizontal)
        self.timeout_slider.setRange(1, 10)
        self.timeout_slider.setValue(5)
        self.timeout_slider.valueChanged.connect(self._on_timeout_changed)
        audio_layout.addWidget(self.timeout_label)
        audio_layout.addWidget(self.timeout_slider)

        self.threshold_label = QLabel("Sensibilidad de silencio: 500")
        self.threshold_slider = QSlider(Qt.Orientation.Horizontal)
        self.threshold_slider.setRange(200, 2000)
        self.threshold_slider.setSingleStep(50)
        self.threshold_slider.setValue(500)
        self.threshold_slider.valueChanged.connect(self._on_threshold_changed)
        audio_layout.addWidget(self.threshold_label)
        audio_layout.addWidget(self.threshold_slider)

        self.input_label = QLabel("Micrófono")
        self.input_label.setObjectName("Muted")
        self.input_combo = QComboBox()
        self.input_combo.addItem("Sistema (por defecto)", "")
        audio_layout.addWidget(self.input_label)
        audio_layout.addWidget(self.input_combo)

        hotkey_card = QWidget()
        hotkey_card.setObjectName("Card")
        hotkey_layout = QVBoxLayout(hotkey_card)
        hotkey_layout.setContentsMargins(12, 12, 12, 12)
        hotkey_layout.setSpacing(8)

        hotkey_title = QLabel("Hotkey")
        hotkey_title.setObjectName("Muted")
        hotkey_layout.addWidget(hotkey_title)

        self.hotkey_status_label = QLabel("Hotkey status: checking...")
        hotkey_layout.addWidget(self.hotkey_status_label)

        self.permissions_button = QPushButton("Abrir permisos (opcional)")
        self.permissions_button.clicked.connect(self.request_permissions_clicked.emit)
        hotkey_layout.addWidget(self.permissions_button)

        self.retry_hotkey_button = QPushButton("Reintentar hotkey")
        self.retry_hotkey_button.clicked.connect(self.retry_hotkey_clicked.emit)
        hotkey_layout.addWidget(self.retry_hotkey_button)

        self.apply_button = QPushButton("Aplicar cambios")
        self.apply_button.clicked.connect(self._emit_settings)

        layout.addWidget(audio_card)
        layout.addWidget(hotkey_card)
        layout.addStretch(1)
        layout.addWidget(self.apply_button)

    def _on_timeout_changed(self, value: int) -> None:
        self.timeout_label.setText(f"Tiempo de silencio: {value}s")

    def _on_threshold_changed(self, value: int) -> None:
        self.threshold_label.setText(f"Sensibilidad de silencio: {value}")

    def _emit_settings(self) -> None:
        selected_device = self.input_combo.currentData()
        if not isinstance(selected_device, str):
            selected_device = ""
        self.settings_changed.emit(
            self.timeout_slider.value(),
            self.threshold_slider.value(),
            selected_device,
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

    def set_input_devices(self, devices: list[str], selected_device: str | None = None) -> None:
        previous = selected_device or ""
        self.input_combo.blockSignals(True)
        self.input_combo.clear()
        self.input_combo.addItem("Sistema (por defecto)", "")
        for device_name in devices:
            self.input_combo.addItem(device_name, device_name)

        index = self.input_combo.findData(previous)
        if index < 0:
            index = 0
        self.input_combo.setCurrentIndex(index)
        self.input_combo.blockSignals(False)
