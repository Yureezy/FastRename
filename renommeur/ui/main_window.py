from __future__ import annotations

import hashlib
import math
from pathlib import Path

from PySide6.QtCore import QSize, Qt, QThread, QTimer, QUrl, Signal
from PySide6.QtGui import (
    QColor,
    QDesktopServices,
    QFontMetrics,
    QIcon,
    QPainter,
    QPen,
    QPixmap,
)
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMenu,
    QMessageBox,
    QPlainTextEdit,
    QProgressDialog,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QSplitter,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from .. import __app_name__, __version__, i18n
from ..config import (
    MAX_SUFFIXES,
    MIN_SUFFIXES,
    REF_IMAGES_DIR,
    AppConfig,
    default_output_dir,
)
from ..renamer import Renamer
from . import style
from .drop_box import DropBox

COLUMNS_PER_ROW = 5
DEBOUNCE_MS = 250


def _flag_icon(code: str) -> QIcon:
    """Dessine un petit drapeau (fiable partout, contrairement aux emojis sur Windows)."""
    w, h = 22, 15
    pm = QPixmap(w, h)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    if code == "fr":  # tricolore vertical
        p.fillRect(0, 0, 7, h, QColor("#0055A4"))
        p.fillRect(7, 0, 8, h, QColor("#ffffff"))
        p.fillRect(15, 0, 7, h, QColor("#EF4135"))
    elif code == "es":  # bandes rouge/jaune/rouge
        p.fillRect(0, 0, w, h, QColor("#AA151B"))
        p.fillRect(0, 4, w, 7, QColor("#F1BF00"))
    elif code == "en":  # croix de Saint-Georges
        p.fillRect(0, 0, w, h, QColor("#ffffff"))
        p.fillRect(0, 6, w, 3, QColor("#CE1124"))
        p.fillRect(9, 0, 4, h, QColor("#CE1124"))
    p.end()
    return QIcon(pm)


def _moon_icon() -> QIcon:
    pm = QPixmap(18, 18)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QColor("#f5d76e"))
    p.drawEllipse(2, 2, 14, 14)
    p.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear)
    p.drawEllipse(6, 0, 14, 14)  # creuse le croissant
    p.end()
    return QIcon(pm)


def _sun_icon() -> QIcon:
    pm = QPixmap(18, 18)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    cx = cy = 9.0
    pen = QPen(QColor("#f6a821"))
    pen.setWidth(2)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    p.setPen(pen)
    for k in range(8):  # 8 rayons
        a = math.pi * k / 4.0
        p.drawLine(
            round(cx + 6 * math.cos(a)), round(cy + 6 * math.sin(a)),
            round(cx + 8.5 * math.cos(a)), round(cy + 8.5 * math.sin(a)),
        )
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QColor("#f6a821"))
    p.drawEllipse(5, 5, 8, 8)  # disque
    p.end()
    return QIcon(pm)


class _ImportWorker(QThread):
    phase = Signal(str)
    progress = Signal(int, int)
    done = Signal(list, list)
    failed = Signal(str)

    def __init__(self, path: str, images_dir: Path, text_col: str, image_col: str, sheet: str) -> None:
        super().__init__()
        self._path = path
        self._images_dir = images_dir
        self._text_col = text_col
        self._image_col = image_col
        self._sheet = sheet

    def run(self) -> None:
        try:
            from ..excel_import import import_references

            self.phase.emit(i18n.t("import_read"))
            refs, warnings = import_references(
                self._path,
                text_column=self._text_col,
                image_column=self._image_col or None,
                sheet_name=self._sheet,
            )
        except Exception as exc:  # noqa: BLE001
            self.failed.emit(str(exc))
            return

        self.phase.emit(i18n.t("import_extract"))
        try:
            self._images_dir.mkdir(parents=True, exist_ok=True)
        except OSError:
            pass

        results: list[tuple[str, str | None]] = []
        total = len(refs)
        for i, ref in enumerate(refs, 1):
            img_path = None
            if ref.image_bytes:
                try:
                    key = hashlib.md5(ref.name.encode("utf-8")).hexdigest()[:16]
                    dest = self._images_dir / f"{key}{ref.image_ext}"
                    dest.write_bytes(ref.image_bytes)
                    img_path = str(dest)
                except OSError:
                    img_path = None
            results.append((ref.name, img_path))
            self.progress.emit(i, total)
        self.done.emit(results, warnings)


class _TitledBox(QGroupBox):
    """QGroupBox avec un petit bouton flottant dans la barre de titre (à droite)."""

    def __init__(self, title: str, corner: QWidget) -> None:
        super().__init__(title)
        self._corner = corner
        corner.setParent(self)
        corner.show()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        f = self.font()
        f.setBold(True)
        title_w = QFontMetrics(f).horizontalAdvance(self.title())
        x = 16 + 8 + title_w + 8 + 10  # left + padding + texte + padding + écart
        self._corner.adjustSize()
        self._corner.move(x, 1)
        self._corner.raise_()


class MainWindow(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.config = AppConfig.load()
        i18n.set_language(self.config.language)
        style.set_theme(self.config.theme)
        app = QApplication.instance()
        if app is not None:
            app.setStyleSheet(style.app_stylesheet())
        self.renamer = Renamer()
        self._drop_boxes: list[DropBox] = []
        self._suffix_edits: list[QLineEdit] = []

        self.setWindowTitle(f"{__app_name__} {__version__}")
        self.resize(1180, 720)
        self._outer = QVBoxLayout(self)
        self._outer.setContentsMargins(0, 0, 0, 0)
        self._content: QWidget | None = None
        self._build()

    def _build(self) -> None:
        # Reconstruit toute l'UI (utilisé aussi au changement de langue).
        # ponytail: un changement de langue réinitialise les suffixes tapés ; action rare, OK.
        if self._content is not None:
            self._content.deleteLater()
        self._drop_boxes = []
        self._suffix_edits = []
        self._content = QWidget()
        self._outer.addWidget(self._content)
        self._build_ui(self._content)
        self._rebuild_grid(self.config.suffix_count)
        self._refresh_undo_button()

    def _build_ui(self, parent: QWidget) -> None:
        root = QVBoxLayout(parent)
        root.setContentsMargins(14, 14, 14, 14)
        root.setSpacing(10)

        # Sélecteur de langue (en haut à droite).
        lang_row = QHBoxLayout()
        lang_row.addStretch(1)

        # Thème : bouton-icône (lune / soleil) centré, menu au clic.
        self.theme_btn = QToolButton()
        self.theme_btn.setObjectName("iconBtn")
        self.theme_btn.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self.theme_btn.setIconSize(QSize(18, 18))
        self.theme_btn.setToolTip(i18n.t("theme"))
        theme_menu = QMenu(self.theme_btn)
        theme_menu.addAction(_moon_icon(), i18n.t("theme_dark")).setData("dark")
        theme_menu.addAction(_sun_icon(), i18n.t("theme_light")).setData("light")
        theme_menu.triggered.connect(lambda a: self._set_theme(a.data()))
        self.theme_btn.setMenu(theme_menu)
        self.theme_btn.setIcon(_moon_icon() if style.current() == "dark" else _sun_icon())
        lang_row.addWidget(self.theme_btn)
        lang_row.addSpacing(8)

        # Langue : bouton-drapeau centré, menu au clic.
        self.lang_btn = QToolButton()
        self.lang_btn.setObjectName("iconBtn")
        self.lang_btn.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self.lang_btn.setIconSize(QSize(22, 15))
        self.lang_btn.setToolTip(i18n.t("language"))
        lang_menu = QMenu(self.lang_btn)
        for code, label in i18n.LANGUAGES.items():
            lang_menu.addAction(_flag_icon(code), label).setData(code)
        lang_menu.triggered.connect(lambda a: self._set_language(a.data()))
        self.lang_btn.setMenu(lang_menu)
        self.lang_btn.setIcon(_flag_icon(i18n.current()))
        lang_row.addWidget(self.lang_btn)
        root.addLayout(lang_row)

        # Options (2) et Journal en haut (60/40).
        top_split = QSplitter(Qt.Orientation.Horizontal)
        top_split.addWidget(self._build_options_box())
        top_split.addWidget(self._build_journal_box())
        top_split.setStretchFactor(0, 3)
        top_split.setStretchFactor(1, 2)
        top_split.setSizes([600, 400])

        # Colonne de droite : (Options | Journal) en haut, cases (3-4) en dessous.
        right_split = QSplitter(Qt.Orientation.Vertical)
        right_split.addWidget(top_split)
        right_split.addWidget(self._build_grid_box())
        right_split.setStretchFactor(0, 0)
        right_split.setStretchFactor(1, 1)
        right_split.setSizes([210, 430])

        # Référence (1) à gauche | colonne de droite.
        self.main_split = QSplitter(Qt.Orientation.Horizontal)
        self.main_split.addWidget(self._build_sidebar())
        self.main_split.addWidget(right_split)
        self.main_split.setStretchFactor(0, 0)
        self.main_split.setStretchFactor(1, 1)
        self.main_split.setCollapsible(0, False)
        self.main_split.setSizes([345, 760])
        self.main_split.splitterMoved.connect(lambda *_: self._update_ref_image())
        root.addWidget(self.main_split, stretch=1)

    def _build_sidebar(self) -> QWidget:
        sidebar = QGroupBox(i18n.t("ref_title"))
        sidebar.setMinimumWidth(150)
        side = QVBoxLayout(sidebar)

        import_btn = QPushButton(i18n.t("import_excel"))
        import_btn.setObjectName("secondary")
        import_btn.setToolTip(i18n.t("import_tip"))
        import_btn.clicked.connect(self._import_excel)
        side.addWidget(import_btn)

        side.addWidget(QLabel(i18n.t("choose_ref")))
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText(i18n.t("search_ph"))
        self.search_edit.setClearButtonEnabled(True)
        self.search_edit.textChanged.connect(self._filter_references)
        side.addWidget(self.search_edit)
        self.ref_list = QListWidget()
        self.ref_list.addItems(self.config.references)
        self.ref_list.currentTextChanged.connect(self._on_reference_changed)
        side.addWidget(self.ref_list, stretch=1)

        self.ref_image = QLabel(i18n.t("no_image"))
        self.ref_image.setObjectName("refImage")
        self.ref_image.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.ref_image.setFixedHeight(150)  # hauteur figée : ne grandit pas avec la fenêtre
        side.addWidget(self.ref_image)

        self.ref_input = QLineEdit()
        self.ref_input.setPlaceholderText(i18n.t("new_ref_ph"))
        self.ref_input.returnPressed.connect(self._add_reference)
        side.addWidget(self.ref_input)

        add_btn = QPushButton(i18n.t("add"))
        add_btn.clicked.connect(self._add_reference)
        side.addWidget(add_btn)

        del_btn = QPushButton(i18n.t("remove"))
        del_btn.setObjectName("danger")
        del_btn.clicked.connect(self._remove_reference)
        clear_all_btn = QPushButton(i18n.t("clear_all"))
        clear_all_btn.setObjectName("danger")
        clear_all_btn.setToolTip(i18n.t("clear_all_tip"))
        clear_all_btn.clicked.connect(self._clear_all_references)
        btn_row = QHBoxLayout()
        btn_row.addWidget(del_btn)
        btn_row.addWidget(clear_all_btn)
        side.addLayout(btn_row)

        self._select_initial_reference()
        self._update_ref_image()
        return sidebar

    def _build_options_box(self) -> QWidget:
        opts_box = QGroupBox(i18n.t("options_title"))
        opts_layout = QGridLayout(opts_box)

        opts_layout.addWidget(QLabel(i18n.t("nb_suffixes")), 0, 0)
        self.count_spin = QSpinBox()
        self.count_spin.setRange(MIN_SUFFIXES, MAX_SUFFIXES)
        self.count_spin.setValue(self.config.suffix_count)
        self.count_spin.setKeyboardTracking(False)
        self.count_spin.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons)
        self.count_spin.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.count_spin.setFixedWidth(60)
        self._count_timer = QTimer(self)
        self._count_timer.setSingleShot(True)
        self._count_timer.setInterval(DEBOUNCE_MS)
        self._count_timer.timeout.connect(self._apply_count)
        self.count_spin.valueChanged.connect(lambda _: self._count_timer.start())

        minus_btn = QPushButton("−")
        minus_btn.setObjectName("counter")
        minus_btn.setFixedWidth(30)
        minus_btn.setToolTip(i18n.t("less_tip"))
        minus_btn.clicked.connect(lambda: self.count_spin.stepBy(-1))
        plus_btn = QPushButton("＋")
        plus_btn.setObjectName("counter")
        plus_btn.setFixedWidth(30)
        plus_btn.setToolTip(i18n.t("more_tip"))
        plus_btn.clicked.connect(lambda: self.count_spin.stepBy(1))

        count_row = QHBoxLayout()
        count_row.setSpacing(6)
        count_row.addWidget(minus_btn)
        count_row.addWidget(self.count_spin)
        count_row.addWidget(plus_btn)
        count_row.addStretch(1)
        opts_layout.addLayout(count_row, 0, 1)

        opts_layout.addWidget(QLabel(i18n.t("output_dir")), 1, 0)
        self.output_edit = QLineEdit(self.config.output_dir)
        self.output_edit.setToolTip(
            i18n.t("output_tip", r=i18n.t("dir_renamed"), o=i18n.t("dir_originals"))
        )
        self.output_edit.editingFinished.connect(self._on_output_changed)
        browse_btn = QPushButton(i18n.t("browse"))
        browse_btn.setObjectName("secondary")
        browse_btn.clicked.connect(self._browse_output)
        open_btn = QPushButton(i18n.t("open"))
        open_btn.setObjectName("secondary")
        open_btn.clicked.connect(self._open_output)
        out_row = QHBoxLayout()
        out_row.addWidget(self.output_edit, stretch=1)
        out_row.addWidget(browse_btn)
        out_row.addWidget(open_btn)
        opts_layout.addLayout(out_row, 1, 1)

        self.preview_check = QCheckBox(i18n.t("preview_check"))
        self.preview_check.setChecked(self.config.preview_before_rename)
        self.preview_check.toggled.connect(self._on_preview_toggled)
        opts_layout.addWidget(self.preview_check, 2, 0, 1, 2)

        self.move_check = QCheckBox(i18n.t("move_check", o=i18n.t("dir_originals")))
        self.move_check.setChecked(self.config.move_originals)
        self.move_check.setToolTip(i18n.t("move_tip", o=i18n.t("dir_originals")))
        self.move_check.toggled.connect(self._on_move_toggled)
        opts_layout.addWidget(self.move_check, 3, 0, 1, 2)

        opts_layout.setColumnStretch(1, 1)
        return opts_box

    def _build_grid_box(self) -> QWidget:
        open_btn = QPushButton("📂")
        open_btn.setObjectName("secondary")
        open_btn.setFixedSize(42, 28)
        open_btn.setToolTip(i18n.t("open_pc_tip"))
        open_btn.clicked.connect(self._open_computer)

        grid_box = _TitledBox(i18n.t("grid_title"), open_btn)
        grid_box_layout = QVBoxLayout(grid_box)
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.grid_host = QWidget()
        self.grid_layout = QGridLayout(self.grid_host)
        self.scroll.setWidget(self.grid_host)
        grid_box_layout.addWidget(self.scroll)
        return grid_box

    def _build_journal_box(self) -> QWidget:
        box = QGroupBox(i18n.t("journal_title"))
        layout = QVBoxLayout(box)

        actions = QHBoxLayout()
        self.undo_btn = QPushButton(i18n.t("undo_btn"))
        self.undo_btn.clicked.connect(self._undo)
        clear_btn = QPushButton(i18n.t("clear_log"))
        clear_btn.setObjectName("secondary")
        clear_btn.clicked.connect(lambda: self.log_view.clear())
        actions.addWidget(self.undo_btn)
        actions.addStretch(1)
        actions.addWidget(clear_btn)
        layout.addLayout(actions)

        self.log_view = QPlainTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setPlaceholderText(i18n.t("log_ph"))
        layout.addWidget(self.log_view, stretch=1)
        return box

    def _rebuild_grid(self, count: int) -> None:
        previous = [edit.text() for edit in self._suffix_edits]

        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        self._drop_boxes.clear()
        self._suffix_edits.clear()

        for i in range(count):
            cell = QWidget()
            cell_layout = QVBoxLayout(cell)
            cell_layout.setContentsMargins(4, 4, 4, 4)

            box = DropBox(i)
            box.filesDropped.connect(self._on_files_dropped)

            suffix_edit = QLineEdit()
            suffix_edit.setPlaceholderText(i18n.t("suffix_ph", n=i + 1))
            suffix_edit.setAlignment(Qt.AlignmentFlag.AlignCenter)
            if i < len(previous):
                suffix_edit.setText(previous[i])

            cell_layout.addWidget(box)
            cell_layout.addWidget(suffix_edit)

            self.grid_layout.addWidget(cell, i // COLUMNS_PER_ROW, i % COLUMNS_PER_ROW)
            self._drop_boxes.append(box)
            self._suffix_edits.append(suffix_edit)

        for c in range(COLUMNS_PER_ROW):
            self.grid_layout.setColumnStretch(c, 1)

    def drop_box_count(self) -> int:
        return len(self._drop_boxes)

    def _apply_count(self) -> None:
        value = self.count_spin.value()
        self.config.suffix_count = value
        self._save_config()
        self._rebuild_grid(value)

    def _set_language(self, code: str) -> None:
        if not code or code == i18n.current():
            return
        i18n.set_language(code)
        self.config.language = code
        self._save_config()
        self._build()  # reconstruit toute l'UI dans la nouvelle langue

    def _set_theme(self, code: str) -> None:
        if not code or code == style.current():
            return
        style.set_theme(code)
        self.config.theme = code
        self._save_config()
        app = QApplication.instance()
        if app is not None:
            app.setStyleSheet(style.app_stylesheet())
        for box in self._drop_boxes:
            box.refresh_theme()
        self.theme_btn.setIcon(_moon_icon() if code == "dark" else _sun_icon())

    def _select_initial_reference(self) -> None:
        target = self.config.last_reference
        if target and target in self.config.references:
            matches = self.ref_list.findItems(target, Qt.MatchFlag.MatchExactly)
            if matches:
                self.ref_list.setCurrentItem(matches[0])
                return
        if self.config.references:
            self.ref_list.setCurrentRow(0)

    def _current_reference(self) -> str:
        item = self.ref_list.currentItem()
        return item.text().strip() if item else ""

    def _on_reference_changed(self, text: str) -> None:
        self.config.last_reference = text.strip()
        self._save_config()
        self._update_ref_image()

    def _add_reference(self) -> None:
        text = self.ref_input.text().strip()
        if not text:
            return
        if text not in self.config.references:
            self.config.references.append(text)
            self.ref_list.addItem(text)
        matches = self.ref_list.findItems(text, Qt.MatchFlag.MatchExactly)
        if matches:
            self.ref_list.setCurrentItem(matches[0])
        self.ref_input.clear()
        self._save_config()

    def _remove_reference(self) -> None:
        item = self.ref_list.currentItem()
        if item is None:
            return
        text = item.text()
        if text in self.config.references:
            self.config.references.remove(text)
        self.config.reference_images.pop(text, None)
        self.ref_list.takeItem(self.ref_list.row(item))
        self._save_config()

    def _clear_all_references(self) -> None:
        if not self.config.references:
            return
        confirm = QMessageBox.question(
            self,
            __app_name__,
            i18n.t("clear_confirm"),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return
        self.config.references.clear()
        self.config.reference_images.clear()
        self.config.last_reference = ""
        self.ref_list.clear()
        self._save_config()
        self._update_ref_image()

    def _filter_references(self, text: str) -> None:
        query = text.strip().casefold()
        for i in range(self.ref_list.count()):
            item = self.ref_list.item(i)
            item.setHidden(query not in item.text().casefold())

    def _update_ref_image(self) -> None:
        name = self._current_reference()
        path = self.config.reference_images.get(name, "") if name else ""
        if path and Path(path).exists():
            pix = QPixmap(path)
            if not pix.isNull():
                # On ajuste à la case sans jamais dépasser la taille d'origine.
                target_w = min(max(1, self.ref_image.width()), pix.width())
                target_h = min(max(1, self.ref_image.height()), pix.height())
                self.ref_image.setPixmap(
                    pix.scaled(
                        target_w,
                        target_h,
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation,
                    )
                )
                self.ref_image.setToolTip(name)
                return
        self.ref_image.setPixmap(QPixmap())
        self.ref_image.setText(i18n.t("no_image"))
        self.ref_image.setToolTip("")

    def _ask_columns(self, sheets: dict[str, list[str]]):
        """Dialogue : onglet + colonne texte + colonne image. Renvoie (sheet, text, image) ou None."""
        from PySide6.QtWidgets import QDialog, QDialogButtonBox, QFormLayout

        dlg = QDialog(self)
        dlg.setWindowTitle(i18n.t("col_dialog_title"))
        form = QFormLayout(dlg)

        sheet_combo = QComboBox()
        sheet_combo.addItems(list(sheets.keys()))
        # Onglet par défaut : celui qui a une colonne ~ "fichier", sinon le plus rempli.
        if sheets:
            best = max(
                sheets,
                key=lambda n: (any("fichier" in h.casefold() for h in sheets[n]), len(sheets[n])),
            )
            sheet_combo.setCurrentText(best)
        text_combo = QComboBox()
        image_combo = QComboBox()

        def populate() -> None:
            headers = sheets.get(sheet_combo.currentText(), [])
            text_combo.clear()
            text_combo.addItems(headers)
            ti = next((i for i, h in enumerate(headers) if "fichier" in h.casefold()), 0)
            text_combo.setCurrentIndex(ti if headers else -1)
            image_combo.clear()
            image_combo.addItem(i18n.t("col_none"), "")
            for h in headers:
                image_combo.addItem(h, h)
            ii = next((i for i, h in enumerate(headers) if "photo" in h.casefold()), -1)
            image_combo.setCurrentIndex(ii + 1 if ii >= 0 else 0)

        populate()
        sheet_combo.currentIndexChanged.connect(populate)

        form.addRow(i18n.t("col_sheet"), sheet_combo)
        form.addRow(i18n.t("col_text"), text_combo)
        form.addRow(i18n.t("col_image"), image_combo)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dlg.accept)
        buttons.rejected.connect(dlg.reject)
        form.addRow(buttons)

        if dlg.exec() != QDialog.DialogCode.Accepted:
            return None
        return sheet_combo.currentText(), text_combo.currentText(), image_combo.currentData()

    def _import_excel(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, i18n.t("import_choose"), str(Path.home()), i18n.t("import_filter")
        )
        if not path:
            return

        from ..excel_import import read_sheets

        try:
            sheets = read_sheets(path)
        except Exception as exc:  # noqa: BLE001
            self._warn(i18n.t("import_fail", err=exc))
            return
        choice = self._ask_columns(sheets)
        if choice is None:
            return
        sheet, text_col, image_col = choice

        self._progress = QProgressDialog(i18n.t("import_read"), None, 0, 0, self)
        self._progress.setWindowTitle(__app_name__)
        self._progress.setWindowModality(Qt.WindowModality.WindowModal)
        self._progress.setMinimumDuration(0)
        self._progress.setAutoClose(False)
        self._progress.setAutoReset(False)
        self._progress.show()

        self._import_worker = _ImportWorker(path, REF_IMAGES_DIR, text_col, image_col, sheet)
        self._import_worker.phase.connect(self._progress.setLabelText)
        self._import_worker.progress.connect(self._on_import_progress)
        self._import_worker.done.connect(self._on_import_done)
        self._import_worker.failed.connect(self._on_import_failed)
        self._import_worker.start()

    def _on_import_progress(self, done: int, total: int) -> None:
        if total and self._progress.maximum() != total:
            self._progress.setRange(0, total)
        self._progress.setValue(done)

    def _on_import_failed(self, message: str) -> None:
        self._progress.close()
        self._warn(i18n.t("import_fail", err=message))

    def _on_import_done(self, results: list, warnings: list) -> None:
        self._progress.close()
        added = 0
        with_image = 0
        for name, img_path in results:
            if name not in self.config.references:
                self.config.references.append(name)
                self.ref_list.addItem(name)
                added += 1
            if img_path:
                self.config.reference_images[name] = img_path
                with_image += 1
        self._save_config()
        if self.ref_list.currentItem() is None and self.ref_list.count():
            self.ref_list.setCurrentRow(0)
        self._update_ref_image()
        self._filter_references(self.search_edit.text())

        msg = i18n.t("import_done", added=added, img=with_image)
        if warnings:
            msg += "\n\n" + "\n".join(warnings)
        QMessageBox.information(self, __app_name__, msg)

    def _on_output_changed(self) -> None:
        self.config.output_dir = self.output_edit.text().strip()
        self._save_config()

    def _browse_output(self) -> None:
        txt = self.output_edit.text().strip()
        start = txt if txt and Path(txt).expanduser().is_dir() else str(Path.home())
        chosen = QFileDialog.getExistingDirectory(self, i18n.t("choose_output"), start)
        if chosen:
            self.output_edit.setText(chosen)
            self._on_output_changed()

    def _open_output(self) -> None:
        path = self._resolved_output_dir()
        try:
            path.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            self._warn(i18n.t("open_output_fail", err=exc))
            return
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))

    def _open_computer(self) -> None:
        # Ouvre l'explorateur au niveau « Ce PC » (tous les disques) pour naviguer.
        import subprocess
        import sys

        try:
            if sys.platform.startswith("win"):
                subprocess.Popen(["explorer", "shell:MyComputerFolder"])
            elif sys.platform == "darwin":
                subprocess.Popen(["open", "/Volumes"])
            else:
                subprocess.Popen(["xdg-open", str(Path.home())])
        except OSError as exc:
            self._warn(i18n.t("explorer_fail", err=exc))

    def _on_preview_toggled(self, checked: bool) -> None:
        self.config.preview_before_rename = checked
        self._save_config()

    def _on_move_toggled(self, checked: bool) -> None:
        self.config.move_originals = checked
        self._save_config()

    def _resolved_output_dir(self) -> Path:
        text = self.output_edit.text().strip() or default_output_dir()
        return Path(text).expanduser()

    def _on_files_dropped(self, index: int, files: list[str]) -> None:
        reference = self._current_reference()
        if not reference:
            self._warn(i18n.t("warn_choose_ref"))
            return

        suffix = self._suffix_edits[index].text().strip()
        if not suffix:
            self._warn(i18n.t("warn_no_suffix", n=index + 1))
            return

        output_dir = self._resolved_output_dir()
        sources = [Path(f) for f in files]

        if self.preview_check.isChecked():
            plan = self.renamer.plan(reference, suffix, output_dir, sources)
            lst = "\n".join(f"  {s.name}  →  {name}" for s, name in plan[:20])
            if len(plan) > 20:
                lst += "\n" + i18n.t("preview_more", n=len(plan) - 20)
            confirm = QMessageBox.question(
                self,
                i18n.t("preview_title"),
                i18n.t(
                    "preview_msg",
                    count=len(plan),
                    dir=output_dir / i18n.t("dir_renamed"),
                    lst=lst,
                ),
                QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel,
            )
            if confirm != QMessageBox.StandardButton.Ok:
                self._log(i18n.t("preview_cancelled"))
                return

        try:
            results = self.renamer.execute(
                reference, suffix, output_dir, sources,
                move_originals=self.move_check.isChecked(),
            )
        except OSError as exc:
            self._warn(i18n.t("write_fail", dir=output_dir, err=exc))
            return

        ok = [r for r in results if r.ok]
        ko = [r for r in results if not r.ok]
        for r in ok:
            self._log(f"✓ {r.source.name}  →  {r.target.name}")
        for r in ko:
            self._log(f"✗ {r.source.name} : {r.error}")

        if ok:
            self._drop_boxes[index].show_preview(str(ok[0].source), len(ok))
        if ko:
            self._warn(i18n.t("ko_files", n=len(ko)))
        self._refresh_undo_button()

    def _undo(self) -> None:
        if not self.renamer.can_undo():
            return
        confirm = QMessageBox.question(
            self,
            i18n.t("undo_title"),
            i18n.t("undo_msg"),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return
        result = self.renamer.undo_last()
        self._log(i18n.t("undo_removed", n=result.removed))
        if result.failed:
            details = "\n".join(str(p) for p, _ in result.failed)
            self._warn(i18n.t("undo_fail", lst=details))
        self._refresh_undo_button()

    def _refresh_undo_button(self) -> None:
        self.undo_btn.setEnabled(self.renamer.can_undo())

    def _save_config(self) -> None:
        try:
            self.config.save()
        except OSError:
            pass  # la sauvegarde des préférences ne doit jamais bloquer l'app

    def _log(self, message: str) -> None:
        self.log_view.appendPlainText(message)

    def _warn(self, message: str) -> None:
        QMessageBox.warning(self, __app_name__, message)

    def closeEvent(self, event):
        self._save_config()
        super().closeEvent(event)
