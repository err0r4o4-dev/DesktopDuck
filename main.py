from __future__ import annotations

import ctypes
import sys

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QMessageBox

from desktop_duck.config import ConfigStore
from desktop_duck.resources import resource_path
from desktop_duck.window import DuckWindow


def _set_windows_app_id() -> None:
    if sys.platform != "win32":
        return
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
            "DesktopDuck.DesktopPet"
        )
    except (AttributeError, OSError):
        pass


def main() -> int:
    _set_windows_app_id()
    app = QApplication(sys.argv)
    app.setApplicationName("DesktopDuck")
    app.setOrganizationName("DesktopDuck")
    app.setQuitOnLastWindowClosed(False)

    icon_path = resource_path("assets", "duck.ico")
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))

    try:
        store = ConfigStore()
        config = store.load()
        store.save(config)
        duck = DuckWindow(config, store)
        duck.show()
    except Exception as error:
        QMessageBox.critical(None, "DesktopDuck", f"เปิด DesktopDuck ไม่สำเร็จ\n\n{error}")
        return 1

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
