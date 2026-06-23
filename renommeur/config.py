from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path

CONFIG_DIR = Path.home() / ".renommeur"
CONFIG_PATH = CONFIG_DIR / "config.json"
REF_IMAGES_DIR = CONFIG_DIR / "ref_images"

DEFAULT_REFERENCES = [
    "VD 1 JKT LEROY",
    "VD 1 OSH 1929 K",
    "VD 1 OSH KUST_",
]

MIN_SUFFIXES = 1
MAX_SUFFIXES = 50


def default_output_dir() -> str:
    # Via l'API Qt : gère le Bureau redirigé (OneDrive) et localisé ; repli sans Qt.
    base = ""
    try:
        from PySide6.QtCore import QStandardPaths

        base = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.DesktopLocation)
        if not base:
            base = QStandardPaths.writableLocation(
                QStandardPaths.StandardLocation.DocumentsLocation
            )
    except Exception:  # noqa: BLE001
        base = ""
    if not base:
        base = str(Path.home() / "Desktop")
    return str(Path(base) / "FastRename")


@dataclass
class AppConfig:
    references: list[str] = field(default_factory=lambda: list(DEFAULT_REFERENCES))
    last_reference: str = ""
    suffix_count: int = 5
    output_dir: str = field(default_factory=default_output_dir)
    preview_before_rename: bool = False
    move_originals: bool = False
    language: str = "fr"
    theme: str = "dark"
    reference_images: dict[str, str] = field(default_factory=dict)

    @classmethod
    def load(cls) -> "AppConfig":
        try:
            data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return cls()
        if not isinstance(data, dict):
            return cls()

        cfg = cls()
        refs = data.get("references")
        if isinstance(refs, list):
            clean = [str(r) for r in refs if isinstance(r, str) and r.strip()]
            if clean:
                cfg.references = clean
        cfg.last_reference = str(data.get("last_reference", cfg.last_reference))
        try:
            cfg.suffix_count = min(
                MAX_SUFFIXES, max(MIN_SUFFIXES, int(data.get("suffix_count", cfg.suffix_count)))
            )
        except (TypeError, ValueError):
            pass
        out = data.get("output_dir")
        if isinstance(out, str) and out.strip():
            cfg.output_dir = out
        # Migration : l'ancien dossier de sortie « Renommés » devient un dossier de
        # base (qui contiendra désormais les sous-dossiers Renommés/ et Originaux/).
        if Path(cfg.output_dir).name.casefold() in ("renommés", "renommes"):
            cfg.output_dir = str(Path(cfg.output_dir).with_name("FastRename"))
        cfg.preview_before_rename = bool(
            data.get("preview_before_rename", cfg.preview_before_rename)
        )
        cfg.move_originals = bool(data.get("move_originals", cfg.move_originals))
        if data.get("language") in ("fr", "en", "es"):
            cfg.language = data["language"]
        if data.get("theme") in ("dark", "light"):
            cfg.theme = data["theme"]
        imgs = data.get("reference_images")
        if isinstance(imgs, dict):
            cfg.reference_images = {
                str(k): str(v) for k, v in imgs.items() if isinstance(v, str)
            }
        return cfg

    def save(self) -> None:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        payload = {
            "references": self.references,
            "last_reference": self.last_reference,
            "suffix_count": self.suffix_count,
            "output_dir": self.output_dir,
            "preview_before_rename": self.preview_before_rename,
            "move_originals": self.move_originals,
            "language": self.language,
            "theme": self.theme,
            "reference_images": self.reference_images,
        }
        # Écriture atomique : temporaire + os.replace -> pas de config tronquée.
        tmp = CONFIG_PATH.with_name(CONFIG_PATH.name + ".tmp")
        tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        os.replace(tmp, CONFIG_PATH)
