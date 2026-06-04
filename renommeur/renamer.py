"""Moteur de copie-renommage sûr.

Mode retenu : **copier puis renommer** — les fichiers d'origine ne sont jamais
touchés. Chaque source est copiée dans le dossier de sortie sous le nom
``référence_suffixe.extension``, avec résolution automatique des collisions.
Chaque lot est journalisé pour permettre une annulation (undo).

Sûreté : la copie est faite en **création exclusive** (``O_EXCL``). Si un fichier
apparaît à la destination entre le calcul du nom et la copie, l'opération échoue
proprement au lieu d'écraser un fichier existant — ce qui empêche aussi l'undo de
supprimer un fichier que l'app n'a pas créé.
"""

from __future__ import annotations

import os
import shutil
from dataclasses import dataclass, field
from pathlib import Path

from .naming import build_target_name, collision_key, resolve_unique


@dataclass
class RenameResult:
    """Résultat de la copie-renommage d'un fichier."""

    source: Path
    target: Path | None
    ok: bool
    error: str = ""


@dataclass
class UndoResult:
    """Résultat d'une annulation."""

    removed: int
    failed: list[tuple[Path, str]] = field(default_factory=list)


@dataclass
class Batch:
    """Un lot exécuté : sert de point d'annulation."""

    created: list[Path] = field(default_factory=list)


def _extended(path: Path) -> str:
    """Sur Windows, préfixe le chemin en ``\\\\?\\`` pour lever la limite MAX_PATH (260).

    Sans effet sur les autres OS. Indispensable quand le dossier de sortie est
    profond (ex. OneDrive) et que le nom complet dépasse 260 caractères.
    """
    raw = os.fspath(path)
    if os.name != "nt":
        return raw
    absolute = os.path.abspath(raw)
    if absolute.startswith("\\\\?\\"):
        return absolute
    if absolute.startswith("\\\\"):  # chemin UNC \\serveur\partage
        return "\\\\?\\UNC\\" + absolute[2:]
    return "\\\\?\\" + absolute


def _copy_exclusive(src: Path, dest: Path) -> None:
    """Copie ``src`` vers ``dest`` en échouant si ``dest`` existe déjà (anti-écrasement)."""
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_BINARY", 0)
    fd = os.open(_extended(dest), flags)  # lève FileExistsError si dest apparaît
    try:
        with os.fdopen(fd, "wb") as fdst, open(_extended(src), "rb") as fsrc:
            shutil.copyfileobj(fsrc, fdst)
    except BaseException:
        # Copie interrompue : on retire le fichier partiel qu'on venait de créer.
        try:
            os.unlink(_extended(dest))
        except OSError:
            pass
        raise
    # Préserve les métadonnées (équivalent de copy2).
    shutil.copystat(_extended(src), _extended(dest))


class Renamer:
    """Effectue les copies-renommages et garde l'historique pour l'undo.

    Une instance vit le temps d'une session. Elle mémorise les noms déjà
    attribués par dossier de sortie pour éviter les collisions entre plusieurs
    dépôts successifs.
    """

    def __init__(self) -> None:
        # clé = dossier de sortie -> ensemble des clés de noms attribués.
        self._taken_by_dir: dict[Path, set[str]] = {}
        self._history: list[Batch] = []

    # ------------------------------------------------------------------ planning
    def plan(
        self,
        reference: str,
        suffix: str,
        output_dir: Path,
        sources: list[Path],
    ) -> list[tuple[Path, str]]:
        """Calcule, sans rien écrire, la liste ``(source, nom_cible)`` du lot (pour l'aperçu)."""
        output_dir = Path(output_dir)
        taken = set(self._taken_by_dir.get(output_dir, set()))
        return self._plan_with(reference, suffix, output_dir, sources, taken)

    def _plan_with(self, reference, suffix, output_dir, sources, taken):
        plan: list[tuple[Path, str]] = []
        for src in sources:
            src = Path(src)
            target_name = build_target_name(reference, suffix, src.name)
            unique = resolve_unique(
                target_name,
                taken,
                existing_on_disk=lambda name: (output_dir / name).exists(),
            )
            plan.append((src, unique))
        return plan

    # ----------------------------------------------------------------- execution
    def execute(
        self,
        reference: str,
        suffix: str,
        output_dir: Path,
        sources: list[Path],
    ) -> list[RenameResult]:
        """Copie chaque source dans ``output_dir`` sous son nom cible.

        Réserve les noms dans la session et enregistre un lot annulable.
        Peut lever ``OSError`` si le dossier de sortie ne peut pas être créé.
        """
        output_dir = Path(output_dir)
        os.makedirs(_extended(output_dir), exist_ok=True)

        taken = self._taken_by_dir.setdefault(output_dir, set())
        plan = self._plan_with(reference, suffix, output_dir, sources, taken)

        results: list[RenameResult] = []
        batch = Batch()
        for src, target_name in plan:
            dest = output_dir / target_name
            try:
                if not src.exists():
                    raise FileNotFoundError("le fichier source a disparu")
                _copy_exclusive(src, dest)
                batch.created.append(dest)
                results.append(RenameResult(src, dest, ok=True))
            except Exception as exc:  # noqa: BLE001 - on remonte l'erreur à l'UI
                # La copie a échoué : on libère le nom réservé.
                taken.discard(collision_key(target_name))
                results.append(RenameResult(src, None, ok=False, error=str(exc)))

        if batch.created:
            self._history.append(batch)
        return results

    # --------------------------------------------------------------------- undo
    def can_undo(self) -> bool:
        return bool(self._history)

    def undo_last(self) -> UndoResult:
        """Supprime les fichiers créés par le dernier lot.

        En cas d'échec partiel (fichier verrouillé/ouvert ailleurs), le lot est
        conservé avec les fichiers restants pour permettre une nouvelle tentative,
        et les échecs sont remontés.
        """
        if not self._history:
            return UndoResult(removed=0)

        batch = self._history[-1]
        removed = 0
        failed: list[tuple[Path, str]] = []
        for path in batch.created:
            try:
                ep = _extended(path)
                if os.path.exists(ep):
                    os.unlink(ep)
                removed += 1
                self._taken_by_dir.get(path.parent, set()).discard(collision_key(path.name))
            except OSError as exc:
                failed.append((path, str(exc)))

        if failed:
            # On garde uniquement les fichiers non supprimés pour un nouvel essai.
            batch.created = [p for p, _ in failed]
        else:
            self._history.pop()
        return UndoResult(removed=removed, failed=failed)
