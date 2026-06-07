from __future__ import annotations

import unicodedata
from pathlib import PurePath

WINDOWS_FORBIDDEN = set('<>:"/\\|?*')

RESERVED_NAMES = {"CON", "PRN", "AUX", "NUL"}
RESERVED_NAMES |= {f"COM{i}" for i in range(1, 10)}
RESERVED_NAMES |= {f"LPT{i}" for i in range(1, 10)}

MAX_NAME_BYTES = 255

DOUBLE_EXTENSIONS = (".tar.gz", ".tar.bz2", ".tar.xz")

REPLACEMENT = "_"
FALLBACK_NAME = "sans_nom"


def split_name_ext(filename: str) -> tuple[str, str]:
    lower = filename.lower()
    for double in DOUBLE_EXTENSIONS:
        if lower.endswith(double) and len(filename) > len(double):
            return filename[: -len(double)], filename[-len(double):]
    p = PurePath(filename)
    if p.suffix and p.stem:
        return p.stem, p.suffix
    return filename, ""


def sanitize_component(text: str) -> str:
    text = unicodedata.normalize("NFC", text)
    text = "".join(" " if unicodedata.category(ch) == "Zs" else ch for ch in text)
    cleaned = []
    for ch in text:
        if ord(ch) < 32 or ch in WINDOWS_FORBIDDEN or unicodedata.category(ch) == "Cf":
            cleaned.append(REPLACEMENT)
        else:
            cleaned.append(ch)
    return "".join(cleaned).strip(" .")


def _truncate_to_bytes(text: str, max_bytes: int) -> str:
    if max_bytes <= 0:
        return ""
    while len(text.encode("utf-8")) > max_bytes and text:
        text = text[:-1]
    return text


def _avoid_reserved(base: str) -> str:
    head = base.split(".")[0]
    if head.upper() in RESERVED_NAMES or base.upper() in RESERVED_NAMES:
        return REPLACEMENT + base
    return base


def build_target_name(reference: str, suffix: str, original_filename: str) -> str:
    ref = sanitize_component(reference)
    suf = sanitize_component(suffix)
    # Pas de double "_" si la référence finit déjà par "_" (ex. "VD 1 JKT LEROY_").
    if ref and suf and not ref.endswith("_") and not suf.startswith("_"):
        base = f"{ref}_{suf}"
    else:
        base = f"{ref}{suf}"
    base = base.strip("_ .")
    base = _avoid_reserved(base)

    _, ext = split_name_ext(original_filename)
    budget = MAX_NAME_BYTES - len(ext.encode("utf-8"))
    base = _truncate_to_bytes(base, budget)
    if not base:
        base = FALLBACK_NAME

    return unicodedata.normalize("NFC", base + ext)


def collision_key(filename: str) -> str:
    return unicodedata.normalize("NFC", filename).casefold()


def resolve_unique(target_name: str, taken: set[str], existing_on_disk) -> str:
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
