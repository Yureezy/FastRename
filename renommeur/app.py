from __future__ import annotations

import sys
import traceback
from pathlib import Path

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QMessageBox

from . import __app_name__
from .ui.main_window import MainWindow


def _logo_path() -> Path | None:
    candidates = []
    mei = getattr(sys, "_MEIPASS", None)  # dossier temporaire d'un build PyInstaller
    if mei:
        candidates.append(Path(mei) / "assets" / "logo.png")
    candidates.append(Path(__file__).resolve().parent.parent / "assets" / "logo.png")
    return next((p for p in candidates if p.is_file()), None)


def _install_excepthook() -> None:
    # Toute erreur non prévue devient un message plutôt qu'un crash silencieux.
    def hook(exc_type, exc, tb):
        traceback.print_exception(exc_type, exc, tb)
        try:
            QMessageBox.critical(
                None, __app_name__, f"Une erreur inattendue est survenue :\n\n{exc}"
            )
        except Exception:  # noqa: BLE001
            pass

    sys.excepthook = hook


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName(__app_name__)
    logo = _logo_path()
    if logo is not None:
        app.setWindowIcon(QIcon(str(logo)))
    _install_excepthook()
    window = MainWindow()

    # --selfcheck : démarre l'UI puis quitte (sert à valider le binaire packagé).
    if "--selfcheck" in sys.argv:
        from PySide6.QtCore import QTimer

        window.show()
        app.processEvents()
        print(f"SELFCHECK_OK cases={window.drop_box_count()}")
        QTimer.singleShot(0, app.quit)
        return app.exec()

    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
