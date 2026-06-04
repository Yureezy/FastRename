"""Fenêtre principale : référence, nombre de suffixes, cases de dépôt, journal."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, QTimer, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from .. import __app_name__, __version__
from ..config import MAX_SUFFIXES, MIN_SUFFIXES, AppConfig, default_output_dir
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
        self.resize(820, 640)
        self._build_ui()
        self._rebuild_grid(self.config.suffix_count)
        self._refresh_undo_button()

    # ----------------------------------------------------------------- UI build
    def _build_ui(self) -> None:
        root = QVBoxLayout(self)

        # --- Référence -----------------------------------------------------
        ref_box = QGroupBox("1 · Référence")
        ref_layout = QHBoxLayout(ref_box)
        self.ref_combo = QComboBox()
        self.ref_combo.setEditable(True)
        self.ref_combo.addItems(self.config.references)
        if self.config.last_reference and self.config.last_reference in self.config.references:
            self.ref_combo.setCurrentText(self.config.last_reference)
        # En mémoire à chaque frappe ; on ne sauvegarde qu'en fin de saisie.
        self.ref_combo.currentTextChanged.connect(self._on_reference_changed)
        self.ref_combo.lineEdit().editingFinished.connect(self._save_config)
        add_btn = QPushButton("＋ Ajouter")
        add_btn.setToolTip("Enregistrer la référence saisie dans la liste")
        add_btn.clicked.connect(self._add_reference)
        del_btn = QPushButton("🗑 Retirer")
        del_btn.setToolTip("Retirer la référence sélectionnée de la liste")
        del_btn.clicked.connect(self._remove_reference)
        ref_layout.addWidget(self.ref_combo, stretch=1)
        ref_layout.addWidget(add_btn)
        ref_layout.addWidget(del_btn)
        root.addWidget(ref_box)

        # --- Nombre de suffixes + dossier de sortie ------------------------
        opts_box = QGroupBox("2 · Options")
        opts_layout = QGridLayout(opts_box)

        opts_layout.addWidget(QLabel("Nombre de suffixes :"), 0, 0)
        self.count_spin = QSpinBox()
        self.count_spin.setRange(MIN_SUFFIXES, MAX_SUFFIXES)
        self.count_spin.setValue(self.config.suffix_count)
        self.count_spin.setKeyboardTracking(False)  # pas de valeurs intermédiaires au clavier
        # Debounce : on ne reconstruit/sauve qu'une fois la valeur stabilisée.
        self._count_timer = QTimer(self)
        self._count_timer.setSingleShot(True)
        self._count_timer.setInterval(DEBOUNCE_MS)
        self._count_timer.timeout.connect(self._apply_count)
        self.count_spin.valueChanged.connect(lambda _: self._count_timer.start())
        opts_layout.addWidget(self.count_spin, 0, 1)

        opts_layout.addWidget(QLabel("Dossier de sortie :"), 1, 0)
        self.output_edit = QLineEdit(self.config.output_dir)
        self.output_edit.editingFinished.connect(self._on_output_changed)
        browse_btn = QPushButton("Parcourir…")
        browse_btn.clicked.connect(self._browse_output)
        open_btn = QPushButton("Ouvrir")
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
        root.addWidget(opts_box)

        # --- Grille des cases ---------------------------------------------
        grid_box = QGroupBox("3 · Suffixes · 4 · Dépose tes images dans les cases")
        grid_box_layout = QVBoxLayout(grid_box)
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.grid_host = QWidget()
        self.grid_layout = QGridLayout(self.grid_host)
        self.scroll.setWidget(self.grid_host)
        grid_box_layout.addWidget(self.scroll)
        root.addWidget(grid_box, stretch=1)

        # --- Journal + actions --------------------------------------------
        actions = QHBoxLayout()
        self.undo_btn = QPushButton("↩ Annuler le dernier lot")
        self.undo_btn.clicked.connect(self._undo)
        clear_btn = QPushButton("Effacer le journal")
        clear_btn.clicked.connect(lambda: self.log_view.clear())
        actions.addWidget(self.undo_btn)
        actions.addStretch(1)
        actions.addWidget(clear_btn)
        root.addLayout(actions)

        self.log_view = QPlainTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setMaximumHeight(150)
        self.log_view.setPlaceholderText("Le journal des renommages s'affichera ici…")
        root.addWidget(self.log_view)

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

    def drop_box_count(self) -> int:
        """Nombre de cases actuellement affichées (API publique, utilisée par le selfcheck)."""
        return len(self._drop_boxes)

    def _apply_count(self) -> None:
        value = self.count_spin.value()
        self.config.suffix_count = value
        self._save_config()
        self._rebuild_grid(value)

    # ----------------------------------------------------------- event handlers
    def _on_reference_changed(self, text: str) -> None:
        # Mise à jour en mémoire seulement ; la persistance a lieu en fin de saisie.
        self.config.last_reference = text.strip()

    def _add_reference(self) -> None:
        text = self.ref_combo.currentText().strip()
        if not text:
            return
        if text not in self.config.references:
            self.config.references.append(text)
            self.ref_combo.addItem(text)
        self.ref_combo.setCurrentText(text)
        self._save_config()

    def _remove_reference(self) -> None:
        text = self.ref_combo.currentText().strip()
        if text in self.config.references:
            self.config.references.remove(text)
            idx = self.ref_combo.findText(text)
            if idx >= 0:
                self.ref_combo.removeItem(idx)
            self._save_config()

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
        reference = self.ref_combo.currentText().strip()
        if not reference:
            self._warn("Choisis d'abord une référence (étape 1).")
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
            self._drop_boxes[index].flash_done(len(ok))
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
