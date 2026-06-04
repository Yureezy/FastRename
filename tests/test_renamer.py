"""Tests du moteur de copie-renommage (utilise des dossiers temporaires)."""

from pathlib import Path

from renommeur.renamer import Renamer


def _make_image(folder: Path, name: str, content: bytes = b"data") -> Path:
    p = folder / name
    p.write_bytes(content)
    return p


def test_copie_renomme_sans_toucher_loriginal(tmp_path):
    src_dir = tmp_path / "src"
    out_dir = tmp_path / "out"
    src_dir.mkdir()
    src = _make_image(src_dir, "photo.jpeg")

    r = Renamer()
    results = r.execute("VD 1 JKT LEROY", "TQG", out_dir, [src])

    assert len(results) == 1 and results[0].ok
    assert src.exists()  # l'original est intact
    assert (out_dir / "VD 1 JKT LEROY_TQG.jpeg").exists()


def test_collision_dans_le_meme_lot(tmp_path):
    src_dir = tmp_path / "src"
    out_dir = tmp_path / "out"
    src_dir.mkdir()
    a = _make_image(src_dir, "a.jpg")
    b = _make_image(src_dir, "b.jpg")

    r = Renamer()
    results = r.execute("REF", "S", out_dir, [a, b])

    assert all(res.ok for res in results)
    names = sorted(p.name for p in out_dir.iterdir())
    assert names == ["REF_S.jpg", "REF_S_1.jpg"]


def test_collision_entre_deux_depots(tmp_path):
    src_dir = tmp_path / "src"
    out_dir = tmp_path / "out"
    src_dir.mkdir()
    a = _make_image(src_dir, "a.jpg")
    b = _make_image(src_dir, "b.jpg")

    r = Renamer()
    r.execute("REF", "S", out_dir, [a])
    r.execute("REF", "S", out_dir, [b])  # même cible -> doit s'incrémenter

    names = sorted(p.name for p in out_dir.iterdir())
    assert names == ["REF_S.jpg", "REF_S_1.jpg"]


def test_undo_supprime_les_copies(tmp_path):
    src_dir = tmp_path / "src"
    out_dir = tmp_path / "out"
    src_dir.mkdir()
    a = _make_image(src_dir, "a.jpg")

    r = Renamer()
    r.execute("REF", "S", out_dir, [a])
    assert (out_dir / "REF_S.jpg").exists()
    assert r.can_undo()

    result = r.undo_last()
    assert result.removed == 1
    assert not (out_dir / "REF_S.jpg").exists()
    assert src_dir.joinpath("a.jpg").exists()  # l'original reste
    assert not r.can_undo()


def test_undo_libere_le_nom(tmp_path):
    src_dir = tmp_path / "src"
    out_dir = tmp_path / "out"
    src_dir.mkdir()
    a = _make_image(src_dir, "a.jpg")
    b = _make_image(src_dir, "b.jpg")

    r = Renamer()
    r.execute("REF", "S", out_dir, [a])
    r.undo_last()
    # Après undo, le nom REF_S.jpg est de nouveau libre.
    r.execute("REF", "S", out_dir, [b])
    assert (out_dir / "REF_S.jpg").exists()


def test_plan_ne_modifie_pas_letat(tmp_path):
    src_dir = tmp_path / "src"
    out_dir = tmp_path / "out"
    src_dir.mkdir()
    a = _make_image(src_dir, "a.jpg")

    r = Renamer()
    plan1 = r.plan("REF", "S", out_dir, [a])
    plan2 = r.plan("REF", "S", out_dir, [a])
    # Deux aperçus successifs donnent le même résultat (pas d'effet de bord).
    assert plan1 == plan2
    assert plan1[0][1] == "REF_S.jpg"
    assert not out_dir.exists()  # aucun fichier écrit
