"""GUI application entry point."""

from __future__ import annotations

import sys

from PySide6 import QtGui, QtWidgets

from .. import config
from ..paths import ASSETS_DIR
from . import theme
from .main_window import MainWindow


def main() -> None:
    app = QtWidgets.QApplication(sys.argv)

    app.setApplicationName("Edition Manager")
    app.setOrganizationName("Edition Manager")
    font = QtGui.QFont("Segoe UI" if sys.platform == "win32" else "Sans Serif", 10)
    app.setFont(font)

    cfg = config.load()
    theme.apply(app, cfg.dark_mode, cfg.primary_color)

    icon_path = ASSETS_DIR / "icon.png"
    if icon_path.exists():
        app.setWindowIcon(QtGui.QIcon(str(icon_path)))

    window = MainWindow()
    window.show()
    sys.exit(app.exec())
