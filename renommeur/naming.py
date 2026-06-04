"""Construction et assainissement des noms de fichiers, multiplateforme Windows + macOS.

On applique partout les règles **Windows** (les plus strictes), qui couvrent macOS.
Voir docs/05-bonnes-pratiques-renommage.md pour le détail et les sources.
"""

from __future__ import annotations

import unicodedata
from pathlib import PurePath

# Les 9 caractères interdits par Windows dans un nom de fichier.
WINDOWS_FORBIDDEN = set('<>:"/\\|?*')

# Noms de périphériques DOS réservés : interdits même avec une extension (NUL.txt == NUL).
RESERVED_NAMES = {"CON", "PRN", "AUX", "NUL"}
RESERVED_NAMES |= {f"COM{i}" for i in range(1, 10)}
RESERVED_NAMES |= {f"LPT{i}" for i in range(1, 10)}

# Limite par composant : 255 octets en UTF-8 (contrainte APFS, la plus stricte).
MAX_NAME_BYTES = 255

# Extensions composées à préserver en entier.
DOUBLE_EXTENSIONS = (".tar.gz", ".tar.bz2", ".tar.xz")

REPLACEMENT = "_"
FALLBACK_NAME = "sans_nom"


def split_name_ext(filename: str) -> tuple[str, str]:
    """Sépare ``(base, extension)`` en préservant l'extension d'origine verbatim.

    Découpe sur le dernier point, sauf pour les doubles extensions connues
    (.tar.gz...). Un fichier caché comme ``.gitignore`` est traité comme un nom
    sans extension.
    """
    lower = filename.lower()
    for double in DOUBLE_EXTENSIONS:
        if lower.endswith(double) and len(filename) > len(double):
            return filename[: -len(double)], filename[-len(double):]
    p = PurePath(filename)
    if p.suffix and p.stem:  # p.stem vide => nom caché type ".gitignore"
        return p.stem, p.suffix
    return filename, ""


def sanitize_component(text: str) -> str:
    """Assainit une portion de nom (référence ou suffixe) selon les règles Windows.

    Retire les caractères interdits et les caractères de contrôle, neutralise les
    caractères de format invisibles (zero-width, overrides bidi), ramène les
    espaces non-ASCII à un espace normal, normalise en NFC, puis enlève les
    espaces/points en bordure.
    """
    text = unicodedata.normalize("NFC", text)
    # Espaces non-ASCII (NBSP, espaces fines...) -> espace normal, pour que le
    # strip final les attrape.
    text = "".join(" " if unicodedata.category(ch) == "Zs" else ch for ch in text)
    cleaned = []
    for ch in text:
        if ord(ch) < 32 or ch in WINDOWS_FORBIDDEN or unicodedata.category(ch) == "Cf":
            cleaned.append(REPLACEMENT)
        else:
            cleaned.append(ch)
    # Windows rejette les espaces/points en bordure de nom.
    return "".join(cleaned).strip(" .")


def _truncate_to_bytes(text: str, max_bytes: int) -> str:
    """Tronque ``text`` pour tenir dans ``max_bytes`` octets UTF-8, sans couper un caractère."""
    if max_bytes <= 0:
        return ""
    while len(text.encode("utf-8")) > max_bytes and text:
        text = text[:-1]
    return text


def _avoid_reserved(base: str) -> str:
    """Préfixe le nom si sa partie significative correspond à un nom réservé DOS."""
    head = base.split(".")[0]
    if head.upper() in RESERVED_NAMES or base.upper() in RESERVED_NAMES:
        return REPLACEMENT + base
    return base


def build_target_name(reference: str, suffix: str, original_filename: str) -> str:
    """Construit le nom cible : ``référence_suffixe`` + extension d'origine.

    Le résultat est assaini, sans underscore orphelin en bordure, sans nom
    réservé, normalisé NFC et tronqué à 255 octets UTF-8 (l'extension n'est
    jamais tronquée).
    """
    ref = sanitize_component(reference)
    suf = sanitize_component(suffix)
    # On insère "_" seulement s'il n'y est pas déjà : une référence comme
    # "VD 1 JKT LEROY_" + "TQG" donne "VD 1 JKT LEROY_TQG" (et non "__").
    if ref and suf and not ref.endswith("_") and not suf.startswith("_"):
        base = f"{ref}_{suf}"
    else:
        base = f"{ref}{suf}"
    # Si un composant est vide, on évite l'underscore traînant/en tête.
    base = base.strip("_ .")
    base = _avoid_reserved(base)

    _, ext = split_name_ext(original_filename)
    budget = MAX_NAME_BYTES - len(ext.encode("utf-8"))
    base = _truncate_to_bytes(base, budget)
    if not base:
        base = FALLBACK_NAME

    return unicodedata.normalize("NFC", base + ext)


def collision_key(filename: str) -> str:
    """Clé de comparaison qui attrape les collisions invisibles.

    Normalise en NFC puis replie la casse : ``Ref_1.JPG`` et ``ref_1.jpg`` ont la
    même clé (ils entrent en conflit sur les systèmes insensibles à la casse).
    """
    return unicodedata.normalize("NFC", filename).casefold()


def resolve_unique(target_name: str, taken: set[str], existing_on_disk) -> str:
    """Rend ``target_name`` unique en insérant ``_1``, ``_2``... avant l'extension.

    ``taken`` est l'ensemble des clés déjà attribuées (mis à jour en place).
    ``existing_on_disk`` est un callable ``(nom) -> bool`` testant la présence sur disque.

    Le suffixe de collision est ajouté en retronquant le radical si nécessaire,
    pour ne jamais repasser au-dessus des 255 octets.
    """
    stem, ext = split_name_ext(target_name)
    ext_bytes = len(ext.encode("utf-8"))
    candidate = target_name
    n = 1
    while collision_key(candidate) in taken or existing_on_disk(candidate):
        marker = f"_{n}"
        budget = MAX_NAME_BYTES - ext_bytes - len(marker.encode("utf-8"))
        candidate = _truncate_to_bytes(stem, budget) + marker + ext
        n += 1
    taken.add(collision_key(candidate))
    return candidate
