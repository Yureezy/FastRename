"""Fenêtre principale : panneaux redimensionnables (référence, options, cases), journal.

Les trois encadrés (1 · Référence, 2 · Options, 3-4 · Suffixes/dépôt) sont placés
dans des QSplitter : l'utilisateur peut ajuster leurs tailles en tirant sur les
séparateurs, comme des fenêtres.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

from PySide6.QtCore import Qt, QTimer, QUrl
from PySide6.QtGui import QDesktopServices, QPixmap
from PySide6.QtWidgets import (
    QCheckBox,
    QFileDialog,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from .. import __app_name__, __version__
from ..config import (
    MAX_SUFFIXES,
    MIN_SUFFIXES,
    REF_IMAGES_DIR,
    AppConfig,
    default_output_dir,
)
from ..renamer import Renamer
from .drop_box import DropBox

# Nombre de cases par ligne dans la grille.
COLUMNS_PER_ROW = 5
# Délai de stabilisation avant de reconstruire la grille / sauver (anti-rafale).
DEBOUNCE_MS = 250


class MainWindow(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.config = AppConfig.load()
        self.renamer = Renamer()
        self._drop_boxes: list[DropBox] = []
        self._suffix_edits: list[QLineEdit] = []

        self.setWindowTitle(f"{__app_name__} {__version__}")
        self.resize(940, 680)
        self._build_ui()
        self._rebuild_grid(self.config.suffix_count)
        self._refresh_undo_button()

    # ----------------------------------------------------------------- UI build
    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(14, 14, 14, 14)
        root.setSpacing(12)

        header = QLabel(f"🏷️  {__app_name__}")
        header.setObjectName("header")
        root.addWidget(header)

        # Colonne de droite : options (2) + grille (3-4) redimensionnables, puis
        # les actions et le journal — alignés SOUS ces panneaux (et non sous la
        # colonne Référence).
        right_split = QSplitter(Qt.Orientation.Vertical)
        right_split.addWidget(self._build_options_box())
        right_split.addWidget(self._build_grid_box())
        right_split.setStretchFactor(0, 0)
        right_split.setStretchFactor(1, 1)
        right_split.setSizes([130, 440])

        right_container = QWidget()
        right_layout = QVBoxLayout(right_container)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(12)
        right_layout.addWidget(right_split, stretch=1)

        actions = QHBoxLayout()
        self.undo_btn = QPushButton("↩ Annuler le dernier lot")
        self.undo_btn.clicked.connect(self._undo)
        clear_btn = QPushButton("Effacer le journal")
        clear_btn.setObjectName("secondary")
        clear_btn.clicked.connect(lambda: self.log_view.clear())
        actions.addWidget(self.undo_btn)
        actions.addStretch(1)
        actions.addWidget(clear_btn)
        right_layout.addLayout(actions)

        self.log_view = QPlainTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setFixedHeight(96)  # petit et figé : ne s'étale jamais
        self.log_view.setPlaceholderText("Le journal des renommages s'affichera ici…")
        right_layout.addWidget(self.log_view)

        # Panneaux redimensionnables : colonne Référence | colonne de droite.
        self.main_split = QSplitter(Qt.Orientation.Horizontal)
        self.main_split.addWidget(self._build_sidebar())
        self.main_split.addWidget(right_container)
        self.main_split.setStretchFactor(0, 0)
        self.main_split.setStretchFactor(1, 1)
        self.main_split.setCollapsible(0, False)
        self.main_split.setSizes([190, 720])
        self.main_split.splitterMoved.connect(lambda *_: self._update_ref_image())
        root.addWidget(self.main_split, stretch=1)

    def _build_sidebar(self) -> QWidget:
        sidebar = QGroupBox("1 · Référence")
        sidebar.setMinimumWidth(150)
        side = QVBoxLayout(sidebar)

        import_btn = QPushButton("📄 Importer un Excel…")
        import_btn.setObjectName("secondary")
        import_btn.setToolTip("Importer des références (et leurs images) depuis un fichier .xlsx")
        import_btn.clicked.connect(self._import_excel)
        side.addWidget(import_btn)

        side.addWidget(QLabel("Choisis ta référence :"))
        self.ref_list = QListWidget()
        self.ref_list.addItems(self.config.references)
        self.ref_list.currentTextChanged.connect(self._on_reference_changed)
        side.addWidget(self.ref_list, stretch=1)

        # Aperçu de l'image associée à la référence sélectionnée.
        self.ref_image = QLabel("(pas d'image)")
        self.ref_image.setObjectName("refImage")
        self.ref_image.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.ref_image.setFixedHeight(150)  # hauteur figée : ne grandit pas avec la fenêtre
        side.addWidget(self.ref_image)

        self.ref_input = QLineEdit()
        self.ref_input.setPlaceholderText("Nouvelle référence…")
        self.ref_input.returnPressed.connect(self._add_reference)
        side.addWidget(self.ref_input)

        add_btn = QPushButton("＋ Ajouter")
        add_btn.clicked.connect(self._add_reference)
        del_btn = QPushButton("🗑 Retirer")
        del_btn.setObjectName("danger")
        del_btn.clicked.connect(self._remove_reference)
        side.addWidget(add_btn)
        side.addWidget(del_btn)

        self._select_initial_reference()
        self._update_ref_image()
        return sidebar

    def _build_options_box(self) -> QWidget:
        opts_box = QGroupBox("2 · Options")
        opts_layout = QGridLayout(opts_box)

        opts_layout.addWidget(QLabel("Nombre de suffixes :"), 0, 0)
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
        minus_btn.setFixedWidth(42)
        minus_btn.setToolTip("Une case de moins")
        minus_btn.clicked.connect(lambda: self.count_spin.stepBy(-1))
        plus_btn = QPushButton("＋")
        plus_btn.setFixedWidth(42)
        plus_btn.setToolTip("Une case de plus")
        plus_btn.clicked.connect(lambda: self.count_spin.stepBy(1))

        count_row = QHBoxLayout()
        count_row.setSpacing(6)
        count_row.addWidget(minus_btn)
        count_row.addWidget(self.count_spin)
        count_row.addWidget(plus_btn)
        count_row.addStretch(1)
        opts_layout.addLayout(count_row, 0, 1)

        opts_layout.addWidget(QLabel("Dossier de sortie :"), 1, 0)
        self.output_edit = QLineEdit(self.config.output_dir)
        self.output_edit.editingFinished.connect(self._on_output_changed)
        browse_btn = QPushButton("Parcourir…")
        browse_btn.setObjectName("secondary")
        browse_btn.clicked.connect(self._browse_output)
        open_btn = QPushButton("Ouvrir")
        open_btn.setObjectName("secondary")
        open_btn.clicked.connect(self._open_output)
        out_row = QHBoxLayout()
        out_row.addWidget(self.output_edit, stretch=1)
        out_row.addWidget(browse_btn)
        out_row.addWidget(open_btn)
        opts_layout.addLayout(out_row, 1, 1)

        self.preview_check = QCheckBox("Demander un aperçu avant de copier")
        self.preview_check.setChecked(self.config.preview_before_rename)
        self.preview_check.toggled.connect(self._on_preview_toggled)
        opts_layout.addWidget(self.preview_check, 2, 0, 1, 2)
        opts_layout.setColumnStretch(1, 1)
        return opts_box

    def _build_grid_box(self) -> QWidget:
        grid_box = QGroupBox("3 · Suffixes  ·  4 · Dépose tes images dans les cases")
        grid_box_layout = QVBoxLayout(grid_box)
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.grid_host = QWidget()
        self.grid_layout = QGridLayout(self.grid_host)
        self.scroll.setWidget(self.grid_host)
        grid_box_layout.addWidget(self.scroll)
        return grid_box

    # --------------------------------------------------------------- grid logic
    def _rebuild_grid(self, count: int) -> None:
        # Mémorise les suffixes déjà saisis pour les préserver.
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
            suffix_edit.setPlaceholderText(f"suffixe {i + 1}")
            suffix_edit.setAlignment(Qt.AlignmentFlag.AlignCenter)
            if i < len(previous):
                suffix_edit.setText(previous[i])

            cell_layout.addWidget(box)
            cell_layout.addWidget(suffix_edit)

            self.grid_layout.addWidget(cell, i // COLUMNS_PER_ROW, i % COLUMNS_PER_ROW)
            self._drop_boxes.append(box)
            self._suffix_edits.append(suffix_edit)

        # Les colonnes s'étirent pour remplir toute la largeur disponible.
        for c in range(COLUMNS_PER_ROW):
            self.grid_layout.setColumnStretch(c, 1)

    def drop_box_count(self) -> int:
        """Nombre de cases actuellement affichées (API publique, utilisée par le selfcheck)."""
        return len(self._drop_boxes)

    def _apply_count(self) -> None:
        value = self.count_spin.value()
        self.config.suffix_count = value
        self._save_config()
        self._rebuild_grid(value)

    # ------------------------------------------------------------ références
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

    def _update_ref_image(self) -> None:
        name = self._current_reference()
        path = self.config.reference_images.get(name, "") if name else ""
        if path and Path(path).exists():
            pix = QPixmap(path)
            if not pix.isNull():
                # On ajuste à la case SANS jamais dépasser la taille d'origine
                # de l'image (donc pas d'agrandissement quand la fenêtre grandit).
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
        self.ref_image.setText("(pas d'image)")
        self.ref_image.setToolTip("")

    def _import_excel(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Importer un fichier Excel", str(Path.home()), "Fichiers Excel (*.xlsx)"
        )
        if not path:
            return
        try:
            from ..excel_import import import_references

            refs, warnings = import_references(path)
        except Exception as exc:  # noqa: BLE001
            self._warn(f"Impossible de lire le fichier Excel :\n{exc}")
            return

        REF_IMAGES_DIR.mkdir(parents=True, exist_ok=True)
        added = 0
        with_image = 0
        for ref in refs:
            if ref.name not in self.config.references:
                self.config.references.append(ref.name)
                self.ref_list.addItem(ref.name)
                added += 1
            if ref.image_bytes:
                key = hashlib.md5(ref.name.encode("utf-8")).hexdigest()[:16]
                dest = REF_IMAGES_DIR / f"{key}{ref.image_ext}"
                try:
                    dest.write_bytes(ref.image_bytes)
                    self.config.reference_images[ref.name] = str(dest)
                    with_image += 1
                except OSError:
                    pass
        self._save_config()
        if self.ref_list.currentItem() is None and self.ref_list.count():
            self.ref_list.setCurrentRow(0)
        self._update_ref_image()

        msg = f"{added} référence(s) ajoutée(s) ({with_image} avec image)."
        if warnings:
            msg += "\n\n" + "\n".join(warnings)
        QMessageBox.information(self, __app_name__, msg)

    # ----------------------------------------------------------- event handlers
    def _on_output_changed(self) -> None:
        self.config.output_dir = self.output_edit.text().strip()
        self._save_config()

    def _browse_output(self) -> None:
        txt = self.output_edit.text().strip()
        start = txt if txt and Path(txt).expanduser().is_dir() else str(Path.home())
        chosen = QFileDialog.getExistingDirectory(self, "Choisir le dossier de sortie", start)
        if chosen:
            self.output_edit.setText(chosen)
            self._on_output_changed()

    def _open_output(self) -> None:
        path = self._resolved_output_dir()
        try:
            path.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            self._warn(f"Impossible d'ouvrir le dossier de sortie :\n{exc}")
            return
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))

    def _on_preview_toggled(self, checked: bool) -> None:
        self.config.preview_before_rename = checked
        self._save_config()

    # -------------------------------------------------------------- core action
    def _resolved_output_dir(self) -> Path:
        """Dossier de sortie effectif : champ saisi (tilde développé) ou défaut."""
        text = self.output_edit.text().strip() or default_output_dir()
        return Path(text).expanduser()

    def _on_files_dropped(self, index: int, files: list[str]) -> None:
        reference = self._current_reference()
        if not reference:
            self._warn("Choisis d'abord une référence (à gauche).")
            return

        suffix = self._suffix_edits[index].text().strip()
        if not suffix:
            self._warn(f"La case {index + 1} n'a pas de suffixe. Saisis-en un sous la case.")
            return

        output_dir = self._resolved_output_dir()
        sources = [Path(f) for f in files]

        if self.preview_check.isChecked():
            plan = self.renamer.plan(reference, suffix, output_dir, sources)
            apercu = "\n".join(f"  {s.name}  →  {name}" for s, name in plan[:20])
            if len(plan) > 20:
                apercu += f"\n  … (+{len(plan) - 20})"
            confirm = QMessageBox.question(
                self,
                "Aperçu du renommage",
                f"Copier {len(plan)} fichier(s) vers :\n{output_dir}\n\n{apercu}",
                QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel,
            )
            if confirm != QMessageBox.StandardButton.Ok:
                self._log("Aperçu annulé.")
                return

        try:
            results = self.renamer.execute(reference, suffix, output_dir, sources)
        except OSError as exc:
            self._warn(f"Impossible d'écrire dans le dossier de sortie :\n{output_dir}\n\n{exc}")
            return

        ok = [r for r in results if r.ok]
        ko = [r for r in results if not r.ok]
        for r in ok:
            self._log(f"✓ {r.source.name}  →  {r.target.name}")
        for r in ko:
            self._log(f"✗ {r.source.name} : {r.error}")

        if ok:
            # Aperçu : on affiche une miniature de la première image copiée.
            self._drop_boxes[index].show_preview(str(ok[0].source), len(ok))
        if ko:
            self._warn(f"{len(ko)} fichier(s) n'ont pas pu être copiés. Voir le journal.")
        self._refresh_undo_button()

    def _undo(self) -> None:
        if not self.renamer.can_undo():
            return
        confirm = QMessageBox.question(
            self,
            "Annuler le dernier lot",
            "Supprimer les fichiers créés par le dernier dépôt ?\n"
            "(Tes images d'origine ne sont jamais touchées.)",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return
        result = self.renamer.undo_last()
        self._log(f"↩ {result.removed} fichier(s) supprimé(s) (annulation).")
        if result.failed:
            details = "\n".join(str(p) for p, _ in result.failed)
            self._warn(
                "Ces fichiers n'ont pas pu être supprimés (peut-être ouverts ailleurs).\n"
                "Ferme-les puis réessaie l'annulation :\n\n" + details
            )
        self._refresh_undo_button()

    def _refresh_undo_button(self) -> None:
        self.undo_btn.setEnabled(self.renamer.can_undo())

    # --------------------------------------------------------------- utilitaires
    def _save_config(self) -> None:
        try:
            self.config.save()
        except OSError:
            pass  # la sauvegarde de préférences ne doit jamais bloquer l'app

    def _log(self, message: str) -> None:
        self.log_view.appendPlainText(message)

    def _warn(self, message: str) -> None:
        QMessageBox.warning(self, __app_name__, message)

    def closeEvent(self, event):
        self._save_config()
        super().closeEvent(event)
