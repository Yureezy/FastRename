from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QFrame, QLabel, QSizePolicy, QVBoxLayout

from .. import i18n
from . import style


class DropBox(QFrame):
    filesDropped = Signal(int, list)

    def __init__(self, index: int) -> None:
        super().__init__()
        self.index = index
        self.setObjectName("dropBox")
        self.setAcceptDrops(True)
        self.setMinimumSize(150, 160)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setStyleSheet(style.drop_idle())
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

        self._caption = QLabel(i18n.t("drop_caption"))
        self._caption.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._caption.setWordWrap(True)
        layout.addWidget(self._caption)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.setStyleSheet(style.drop_hover())
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dragLeaveEvent(self, event):  # noqa: ARG002
        self.refresh_theme()

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
            self.refresh_theme()
            self._caption.setText(i18n.t("drop_invalid"))
            event.ignore()

    def show_preview(self, image_path: str, count: int) -> None:
        pix = QPixmap(image_path)
        if not pix.isNull():
            self._pixmap = pix
            self._update_pixmap()
        self._caption.setText(i18n.t("drop_done", n=count))
        self.setStyleSheet(style.drop_done())
        self.setToolTip(i18n.t("drop_tooltip", n=count, p=image_path))

    def refresh_theme(self) -> None:
        self.setStyleSheet(style.drop_done() if self._pixmap else style.drop_idle())

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
