"""Test d'intégration de l'interface en mode offscreen (sans écran réel).

Construit la fenêtre, simule un dépôt de fichier et vérifie que la copie a lieu.
"""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest

pytest.importorskip("PySide6")

from PySide6.QtTest import QTest  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

from renommeur.ui.main_window import DEBOUNCE_MS, MainWindow  # noqa: E402


@pytest.fixture(scope="module")
def app():
    application = QApplication.instance() or QApplication([])
    yield application


def test_fenetre_se_construit(app):
    win = MainWindow()
    # 5 cases par défaut.
    assert len(win._drop_boxes) == win.count_spin.value()
    assert len(win._suffix_edits) == len(win._drop_boxes)


def test_changement_du_nombre_de_suffixes(app):
    win = MainWindow()
    # La reconstruction de la grille est debouncée : on laisse le timer se déclencher.
    win.count_spin.setValue(8)
    QTest.qWait(DEBOUNCE_MS + 150)
    assert win.drop_box_count() == 8
    win.count_spin.setValue(3)
    QTest.qWait(DEBOUNCE_MS + 150)
    assert win.drop_box_count() == 3


def test_depot_simule_copie_le_fichier(app, tmp_path):
    win = MainWindow()
    # Ajoute (si besoin) et sélectionne la référence dans la liste latérale.
    win.ref_input.setText("VD 1 JKT LEROY")
    win._add_reference()
    win.count_spin.setValue(5)
    QTest.qWait(DEBOUNCE_MS + 150)  # laisse le debounce reconstruire la grille
    win._suffix_edits[2].setText("TQG")
    out_dir = tmp_path / "out"
    win.output_edit.setText(str(out_dir))

    src = tmp_path / "photo.jpeg"
    src.write_bytes(b"img")

    # Simule le signal émis par la case n°2.
    win._on_files_dropped(2, [str(src)])

    assert (out_dir / "VD 1 JKT LEROY_TQG.jpeg").exists()
    assert src.exists()  # original intact
    assert win.renamer.can_undo()
