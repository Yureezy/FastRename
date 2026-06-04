"""Tests des correctifs issus de la revue de code adversariale."""

import json

from renommeur.config import AppConfig
from renommeur.naming import (
    build_target_name,
    resolve_unique,
    sanitize_component,
)
from renommeur.renamer import Renamer


# --- naming -----------------------------------------------------------------
def test_collision_ne_depasse_pas_255_octets():
    # Nom déjà au plafond : l'ajout du suffixe de collision doit retronquer.
    stem = "a" * 251  # 251 + ".jpg" = 255 octets
    base = build_target_name(stem, "", "x.jpg")
    assert len(base.encode("utf-8")) <= 255

    taken = {base.casefold()}  # force une collision
    unique = resolve_unique(base, taken, existing_on_disk=lambda n: False)
    assert unique != base
    assert len(unique.encode("utf-8")) <= 255
    assert unique.endswith(".jpg")


def test_suffixe_vide_pas_underscore_trainant():
    assert build_target_name("VD 1 JKT LEROY", "", "photo.jpeg") == "VD 1 JKT LEROY.jpeg"


def test_reference_vide_pas_underscore_en_tete():
    assert build_target_name("", "TQG", "photo.jpeg") == "TQG.jpeg"


def test_filtre_caracteres_invisibles():
    # RLO (U+202E, override bidi) et ZWSP (U+200B) doivent disparaître.
    out = sanitize_component("a‮b​c")
    assert "‮" not in out and "​" not in out


def test_nbsp_final_strippe():
    # NBSP (U+00A0) en fin doit être retiré comme un espace normal.
    assert sanitize_component("REF ") == "REF"


# --- renamer : anti-écrasement + undo ---------------------------------------
def test_copie_n_ecrase_pas_un_fichier_existant(tmp_path):
    src_dir = tmp_path / "src"
    out_dir = tmp_path / "out"
    src_dir.mkdir()
    out_dir.mkdir()
    src = src_dir / "a.jpg"
    src.write_bytes(b"nouveau")

    # Un fichier porte déjà le nom cible exact.
    existing = out_dir / "REF_S.jpg"
    existing.write_bytes(b"ancien")

    r = Renamer()
    results = r.execute("REF", "S", out_dir, [src])
    # La collision est résolue -> le fichier existant n'est PAS écrasé.
    assert existing.read_bytes() == b"ancien"
    assert results[0].ok
    assert results[0].target.name == "REF_S_1.jpg"


def test_undo_partiel_conserve_le_lot(tmp_path, monkeypatch):
    src_dir = tmp_path / "src"
    out_dir = tmp_path / "out"
    src_dir.mkdir()
    a = src_dir / "a.jpg"
    a.write_bytes(b"x")

    r = Renamer()
    r.execute("REF", "S", out_dir, [a])

    # Simule un verrou : la suppression échoue.
    import os

    def boom(_path):
        raise OSError("fichier verrouillé")

    monkeypatch.setattr(os, "unlink", boom)
    result = r.undo_last()
    assert result.removed == 0
    assert result.failed  # l'échec est remonté
    assert r.can_undo()   # le lot est conservé pour réessayer


# --- config : tolérance ------------------------------------------------------
def test_config_json_non_objet_ne_plante_pas(tmp_path, monkeypatch):
    import renommeur.config as cfgmod

    path = tmp_path / "config.json"
    path.write_text("[1, 2, 3]", encoding="utf-8")  # JSON valide mais pas un objet
    monkeypatch.setattr(cfgmod, "CONFIG_PATH", path)
    cfg = AppConfig.load()  # ne doit pas lever
    assert cfg.references  # retombe sur les défauts


def test_config_borne_suffix_count(tmp_path, monkeypatch):
    import renommeur.config as cfgmod

    path = tmp_path / "config.json"
    path.write_text(json.dumps({"suffix_count": 100000}), encoding="utf-8")
    monkeypatch.setattr(cfgmod, "CONFIG_PATH", path)
    cfg = AppConfig.load()
    assert cfg.suffix_count == cfgmod.MAX_SUFFIXES


def test_config_save_atomique(tmp_path, monkeypatch):
    import renommeur.config as cfgmod

    monkeypatch.setattr(cfgmod, "CONFIG_DIR", tmp_path)
    monkeypatch.setattr(cfgmod, "CONFIG_PATH", tmp_path / "config.json")
    cfg = AppConfig()
    cfg.references = ["A", "B"]
    cfg.save()
    reloaded = AppConfig.load()
    assert reloaded.references == ["A", "B"]
    assert not (tmp_path / "config.json.tmp").exists()  # le temporaire a été remplacé
