"""Point d'entrée applicatif : crée la QApplication et affiche la fenêtre."""

from __future__ import annotations

import sys
import traceback

from PySide6.QtWidgets import QApplication, QMessageBox

from . import __app_name__
from .ui.main_window import MainWindow
from .ui.style import STYLESHEET


def _install_excepthook() -> None:
    """Filet de sécurité : une erreur non prévue devient un message, pas un crash silencieux."""

    def hook(exc_type, exc, tb):
        traceback.print_exception(exc_type, exc, tb)
        try:
            QMessageBox.critical(
                None, __app_name__, f"Une erreur inattendue est survenue :\n\n{exc}"
            )
        except Exception:  # noqa: BLE001 - on ne masque jamais l'erreur d'origine
            pass

    sys.excepthook = hook


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName(__app_name__)
    app.setStyleSheet(STYLESHEET)
    _install_excepthook()
    window = MainWindow()

    # Mode de vérification : construit l'UI, traite quelques événements, puis quitte.
    # Sert à valider qu'un exécutable packagé (PyInstaller) démarre Qt correctement.
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
