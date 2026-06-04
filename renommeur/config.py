"""Chargement / sauvegarde de la configuration utilisateur (références, options).

Stockée en JSON dans ``~/.renommeur/config.json`` — éditable depuis l'app.
Lecture tolérante (un fichier corrompu retombe sur les valeurs par défaut) et
écriture atomique (fichier temporaire + ``os.replace``).
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path

CONFIG_DIR = Path.home() / ".renommeur"
CONFIG_PATH = CONFIG_DIR / "config.json"
# Images des références importées depuis Excel (extraites sur le disque).
REF_IMAGES_DIR = CONFIG_DIR / "ref_images"

DEFAULT_REFERENCES = [
    "VD 1 JKT LEROY",
    "VD 1 OSH 1929 K",
    "VD 1 OSH KUST_",
]

MIN_SUFFIXES = 1
MAX_SUFFIXES = 50


def default_output_dir() -> str:
    """Dossier de sortie par défaut : ``<Bureau>/Renommés``.

    Passe par l'API Qt des dossiers connus, qui résout correctement le Bureau
    même quand il est redirigé (OneDrive « Known Folder Move ») ou localisé.
    Repli défensif si Qt n'est pas disponible (tests sans QApplication).
    """
    base = ""
    try:
        from PySide6.QtCore import QStandardPaths

        base = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.DesktopLocation)
        if not base:
            base = QStandardPaths.writableLocation(
                QStandardPaths.StandardLocation.DocumentsLocation
            )
    except Exception:  # noqa: BLE001 - pas de Qt -> repli
        base = ""
    if not base:
        base = str(Path.home() / "Desktop")
    return str(Path(base) / "Renommés")


@dataclass
class AppConfig:
    references: list[str] = field(default_factory=lambda: list(DEFAULT_REFERENCES))
    last_reference: str = ""
    suffix_count: int = 5
    output_dir: str = field(default_factory=default_output_dir)
    preview_before_rename: bool = False
    # nom de référence -> chemin de son image (importée depuis Excel)
    reference_images: dict[str, str] = field(default_factory=dict)

    # --------------------------------------------------------------- persistence
    @classmethod
    def load(cls) -> "AppConfig":
        try:
            data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return cls()
        if not isinstance(data, dict):  # JSON valide mais non-objet (liste, scalaire…)
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
        cfg.preview_before_rename = bool(
            data.get("preview_before_rename", cfg.preview_before_rename)
        )
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
            "reference_images": self.reference_images,
        }
        # Écriture atomique : on écrit dans un temporaire du même dossier, puis on
        # remplace d'un coup -> jamais de config.json tronqué en cas d'interruption.
        tmp = CONFIG_PATH.with_name(CONFIG_PATH.name + ".tmp")
        tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        os.replace(tmp, CONFIG_PATH)
