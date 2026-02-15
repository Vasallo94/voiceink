import os
import sys

from PySide6.QtGui import QIcon


def resource_path(relative_path: str) -> str:
    try:
        base_path = getattr(sys, "_MEIPASS", os.path.abspath("."))
    except Exception:
        base_path = os.path.abspath(".")

    path = os.path.join(base_path, relative_path)
    if os.path.exists(path):
        return path

    if getattr(sys, "frozen", False):
        resources_path = os.path.join(
            os.path.dirname(sys.executable), "..", "Resources", relative_path
        )
        if os.path.exists(resources_path):
            return os.path.abspath(resources_path)

    return path


def load_tray_icons() -> dict[str, QIcon]:
    icons = {
        "IDLE": QIcon(resource_path("src/icons/icon_idle_Template.png")),
        "RECORDING": QIcon(resource_path("src/icons/icon_rec_Template.png")),
        "PROCESSING": QIcon(resource_path("src/icons/icon_process_Template.png")),
        "SUCCESS": QIcon(resource_path("src/icons/icon_success_Template.png")),
    }

    for icon in icons.values():
        icon.setIsMask(True)

    return icons
