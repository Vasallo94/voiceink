from PySide6.QtCore import QPoint
from PySide6.QtGui import QAction, QCursor
from PySide6.QtWidgets import QMenu, QSystemTrayIcon

from .resources import load_tray_icons


class TrayManager:
    def __init__(self, popover, on_toggle, on_quit) -> None:
        self.popover = popover
        self.on_toggle = on_toggle
        self.on_quit = on_quit

        self.icons = load_tray_icons()

        self.tray = QSystemTrayIcon()
        self.tray.setIcon(self.icons["IDLE"])
        self.tray.setVisible(True)

        self.menu = QMenu()
        self.action_toggle = QAction("Start/Stop Recording (Ctrl x2)")
        self.action_quit = QAction("Quit")

        self.action_toggle.triggered.connect(self.on_toggle)
        self.action_quit.triggered.connect(self.on_quit)

        self.menu.addAction(self.action_toggle)
        self.menu.addSeparator()
        self.menu.addAction(self.action_quit)

        self.tray.activated.connect(self._on_activated)

    def _on_activated(self, reason) -> None:
        if reason == QSystemTrayIcon.ActivationReason.Context:
            self.menu.popup(QCursor.pos())
            return

        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            rect = self.tray.geometry()
            origin = QPoint(rect.x() - 260, rect.y() + rect.height() + 6)
            self.popover.toggle_near(origin)

    def set_state_icon(self, state_name: str) -> None:
        if state_name == "RECORDING":
            self.tray.setIcon(self.icons["RECORDING"])
            return
        if state_name == "PROCESSING":
            self.tray.setIcon(self.icons["PROCESSING"])
            return
        self.tray.setIcon(self.icons["IDLE"])

    def show_message(self, title: str, subtitle: str, message: str) -> None:
        content = f"{subtitle}\n{message}" if subtitle else message
        self.tray.showMessage(title, content, QSystemTrayIcon.MessageIcon.Information, 2200)

    def show_success_flash(self) -> None:
        self.tray.setIcon(self.icons["SUCCESS"])
