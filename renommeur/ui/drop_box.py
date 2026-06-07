from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QFrame, QLabel, QSizePolicy, QVBoxLayout

from .style import DROP_DONE, DROP_HOVER, DROP_IDLE


class DropBox(QFrame):
    filesDropped = Signal(int, list)

    def __init__(self, index: int) -> None:
        super().__init__()
        self.index = index
        self.setObjectName("dropBox")
        self.setAcceptDrops(True)
        self.setMinimumSize(150, 160)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setStyleSheet(DROP_IDLE)
        self._pixmap: QPixmap | None = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(4)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Politique Ignored : la mise à l'échelle du pixmap ne fait pas grossir la case.
        self._image = QLabel("⬇")
        self._image.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._image.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Ignored)
        layout.addWidget(self._image, stretch=1)

        self._caption = QLabel("Déposez vos images")
        self._caption.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._caption.setWordWrap(True)
        layout.addWidget(self._caption)

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
        self.setStyleSheet(DROP_DONE if self._pixmap else DROP_IDLE)

    def dropEvent(self, event):
        paths = [
            url.toLocalFile()
            for url in event.mimeData().urls()
            if url.isLocalFile()
        ]
        files = [p for p in paths if p and Path(p).is_file()]
        if files:
            self.filesDropped.emit(self.index, files)
            event.acceptProposedAction()
        else:
            self.setStyleSheet(DROP_DONE if self._pixmap else DROP_IDLE)
            self._caption.setText("Aucune image valide — réessaie")
            event.ignore()

    def show_preview(self, image_path: str, count: int) -> None:
        pix = QPixmap(image_path)
        if not pix.isNull():
            self._pixmap = pix
            self._update_pixmap()
        self._caption.setText(f"✓ {count} copié(s) — redéposez")
        self.setStyleSheet(DROP_DONE)
        self.setToolTip(f"{count} image(s) copiée(s)\nDernière : {image_path}")

    def _update_pixmap(self) -> None:
        if self._pixmap and not self._pixmap.isNull():
            self._image.setPixmap(
                self._pixmap.scaled(
                    max(1, self._image.width()),
                    max(1, self._image.height()),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )

    def resizeEvent(self, event):
        self._update_pixmap()
        super().resizeEvent(event)
