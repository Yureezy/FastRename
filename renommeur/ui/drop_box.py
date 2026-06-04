"""La case de dépôt : reçoit le drag & drop et récupère le chemin réel des fichiers.

C'est ici que se joue la fonction centrale du logiciel (voir docs/02-drag-and-drop.md).
``url.toLocalFile()`` donne directement le chemin disque absolu, prêt à être copié.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout

from .style import DROP_DONE, DROP_HOVER, DROP_IDLE


class DropBox(QFrame):
    """Zone de dépôt. Émet ``filesDropped(index, [chemins])`` quand on lâche des fichiers."""

    filesDropped = Signal(int, list)

    def __init__(self, index: int) -> None:
        super().__init__()
        self.index = index
        self.setObjectName("dropBox")
        self.setAcceptDrops(True)
        self.setMinimumSize(120, 96)
        self.setStyleSheet(DROP_IDLE)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._label = QLabel("⬇\nDéposez\nvos images")
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._label)

    # -- drag & drop ---------------------------------------------------------
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.setStyleSheet(DROP_HOVER)
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dragLeaveEvent(self, event):  # noqa: ARG002
        self.setStyleSheet(DROP_IDLE)

    def dropEvent(self, event):
        self.setStyleSheet(DROP_IDLE)
        paths = [
            url.toLocalFile()
            for url in event.mimeData().urls()
            if url.isLocalFile()
        ]
        # On ne garde que les fichiers réels (on ignore les dossiers).
        files = [p for p in paths if p and Path(p).is_file()]
        if files:
            self.filesDropped.emit(self.index, files)
            event.acceptProposedAction()
        else:
            # Rien d'exploitable : on ne prétend pas avoir accepté le drop.
            self._label.setText("Aucune image valide\n— réessaie")
            event.ignore()

    def flash_done(self, count: int) -> None:
        """Retour visuel vert après une copie réussie."""
        self.setStyleSheet(DROP_DONE)
        self._label.setText(f"✓ {count} copié(s)\n— déposez encore")
