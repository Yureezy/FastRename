"""Tests des traductions et du nommage des dossiers selon la langue."""

from renommeur import i18n
from renommeur.renamer import Renamer


def test_toutes_les_chaines_ont_les_trois_langues():
    for key, entry in i18n.STRINGS.items():
        assert {"fr", "en", "es"} <= set(entry), f"clé incomplète : {key}"


def test_t_formate_et_se_replie():
    i18n.set_language("en")
    try:
        assert i18n.t("dir_renamed") == "Renamed"
        assert i18n.t("suffix_ph", n=3) == "suffix 3"
        assert i18n.t("cle_inconnue") == "cle_inconnue"  # repli sur la clé
    finally:
        i18n.set_language("fr")


def test_les_dossiers_suivent_la_langue(tmp_path):
    src = tmp_path / "a.jpg"
    src.write_bytes(b"x")
    out = tmp_path / "out"
    i18n.set_language("es")
    try:
        Renamer().execute("REF", "S", out, [src])
        assert (out / "Renombrados" / "REF_S.jpg").exists()
    finally:
        i18n.set_language("fr")
