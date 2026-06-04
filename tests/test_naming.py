"""Tests de la logique de nommage (aucune dépendance à l'interface)."""

import unicodedata

from renommeur.naming import (
    build_target_name,
    collision_key,
    resolve_unique,
    sanitize_component,
    split_name_ext,
)


def test_cas_nominal_du_cahier_des_charges():
    # L'exemple exact donné par l'utilisateur.
    assert build_target_name("VD 1 JKT LEROY", "TQG", "photo.jpeg") == "VD 1 JKT LEROY_TQG.jpeg"


def test_extension_preservee_verbatim():
    assert build_target_name("REF", "S", "image.JPG") == "REF_S.JPG"
    assert build_target_name("REF", "S", "image.jpeg") == "REF_S.jpeg"


def test_fichier_sans_extension():
    assert build_target_name("REF", "S", "LISEZMOI") == "REF_S"


def test_double_extension():
    assert split_name_ext("archive.tar.gz") == ("archive", ".tar.gz")
    assert build_target_name("REF", "S", "archive.tar.gz") == "REF_S.tar.gz"


def test_fichier_cache_sans_extension():
    assert split_name_ext(".gitignore") == (".gitignore", "")


def test_caracteres_interdits_remplaces():
    out = sanitize_component('a/b:c*d?e"f<g>h|i\\j')
    for forbidden in '/:*?"<>|\\':
        assert forbidden not in out


def test_espaces_et_points_en_fin_strippes():
    assert sanitize_component("REF.  ") == "REF"
    assert sanitize_component("REF...") == "REF"


def test_nom_reserve_dos_prefixe():
    # NUL.txt équivaut à NUL côté Windows -> doit être neutralisé.
    name = build_target_name("NUL", "", "x.txt")
    assert not name.upper().startswith("NUL.")


def test_normalisation_nfc():
    # 'é' décomposé (NFD) doit ressortir composé (NFC).
    decompose = "Café"  # "Café" en NFD
    out = sanitize_component(decompose)
    assert out == unicodedata.normalize("NFC", out)
    assert out == "Café"


def test_troncature_255_octets_preserve_extension():
    longue_ref = "é" * 300  # 'é' = 2 octets en UTF-8 -> ~600 octets
    name = build_target_name(longue_ref, "S", "x.jpeg")
    assert len(name.encode("utf-8")) <= 255
    assert name.endswith(".jpeg")  # l'extension n'est jamais tronquée


def test_collision_key_insensible_casse():
    assert collision_key("Ref_1.JPG") == collision_key("ref_1.jpg")


def test_resolve_unique_incremente_avant_extension():
    taken: set[str] = set()
    on_disk = lambda name: False  # noqa: E731
    assert resolve_unique("REF_S.jpg", taken, on_disk) == "REF_S.jpg"
    # Deuxième fois : même nom -> suffixe numérique inséré avant l'extension.
    assert resolve_unique("REF_S.jpg", taken, on_disk) == "REF_S_1.jpg"
    assert resolve_unique("REF_S.jpg", taken, on_disk) == "REF_S_2.jpg"


def test_resolve_unique_tient_compte_du_disque():
    taken: set[str] = set()
    on_disk = lambda name: name == "REF_S.jpg"  # noqa: E731
    assert resolve_unique("REF_S.jpg", taken, on_disk) == "REF_S_1.jpg"
