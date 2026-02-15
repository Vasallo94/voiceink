from PySide6.QtGui import QPalette
from PySide6.QtWidgets import QApplication


def is_dark_mode(app: QApplication) -> bool:
    palette = app.palette()
    bg = palette.color(QPalette.ColorRole.Window)
    return bg.lightness() < 128


def apply_theme(app: QApplication) -> None:
    dark = is_dark_mode(app)

    if dark:
        bg = "#1E1E1E"
        card = "#2A2A2A"
        text = "#FFFFFF"
        muted = "#A0A0A0"
        border = "#3A3A3A"
    else:
        bg = "#F5F5F7"
        card = "#FFFFFF"
        text = "#1D1D1F"
        muted = "#6E6E73"
        border = "#D2D2D7"

    accent = "#007AFF"

    app.setStyleSheet(
        f"""
        QWidget {{
            color: {text};
            background-color: {bg};
            font-size: 13px;
        }}

        #Card {{
            background-color: {card};
            border: 1px solid {border};
            border-radius: 12px;
        }}

        QPushButton {{
            background-color: {card};
            border: 1px solid {border};
            border-radius: 10px;
            padding: 8px 12px;
        }}

        QPushButton#RecordButton {{
            background-color: {accent};
            color: white;
            border: none;
            border-radius: 24px;
            font-weight: 600;
            min-height: 48px;
        }}

        QPushButton#RecordButton[recording=\"true\"] {{
            background-color: #FF3B30;
        }}

        QLabel#Muted {{
            color: {muted};
        }}

        QListWidget {{
            background-color: {card};
            border: 1px solid {border};
            border-radius: 10px;
        }}

        QTabBar::tab {{
            padding: 8px 12px;
            border: none;
            color: {muted};
        }}

        QTabBar::tab:selected {{
            color: {accent};
            font-weight: 600;
        }}
        """
    )
