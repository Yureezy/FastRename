from __future__ import annotations

import os
import shutil
from dataclasses import dataclass, field
from pathlib import Path

from .naming import build_target_name, collision_key, resolve_unique, split_name_ext

# Sous-dossiers créés dans le dossier de sortie choisi par l'utilisateur.
SUBDIR_RENAMED = "Renommés"
SUBDIR_ORIGINALS = "Originaux"


@dataclass
class RenameResult:
    source: Path
    target: Path | None
    ok: bool
    error: str = ""


@dataclass
class UndoResult:
    removed: int
    failed: list[tuple[Path, str]] = field(default_factory=list)


@dataclass
class Batch:
    created: list[Path] = field(default_factory=list)
    # (emplacement d'origine, nouvel emplacement) des originaux déplacés.
    moved: list[tuple[Path, Path]] = field(default_factory=list)


def _extended(path: Path) -> str:
    # Sur Windows, préfixe en \\?\ pour lever la limite MAX_PATH (260).
    raw = os.fspath(path)
    if os.name != "nt":
        return raw
    absolute = os.path.abspath(raw)
    if absolute.startswith("\\\\?\\"):
        return absolute
    if absolute.startswith("\\\\"):
        return "\\\\?\\UNC\\" + absolute[2:]
    return "\\\\?\\" + absolute


def _copy_exclusive(src: Path, dest: Path) -> None:
    # O_EXCL : échoue (FileExistsError) si dest existe déjà -> jamais d'écrasement.
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_BINARY", 0)
    fd = os.open(_extended(dest), flags)
    try:
        with os.fdopen(fd, "wb") as fdst, open(_extended(src), "rb") as fsrc:
            shutil.copyfileobj(fsrc, fdst)
    except BaseException:
        try:
            os.unlink(_extended(dest))
        except OSError:
            pass
        raise
    shutil.copystat(_extended(src), _extended(dest))


def _unique_in_dir(dest_dir: Path, name: str) -> Path:
    stem, ext = split_name_ext(name)
    candidate = dest_dir / name
    n = 1
    while candidate.exists():
        candidate = dest_dir / f"{stem}_{n}{ext}"
        n += 1
    return candidate


class Renamer:
    def __init__(self) -> None:
        self._taken_by_dir: dict[Path, set[str]] = {}
        self._history: list[Batch] = []

    def plan(
        self,
        reference: str,
        suffix: str,
        output_dir: Path,
        sources: list[Path],
    ) -> list[tuple[Path, str]]:
        renamed_dir = Path(output_dir) / SUBDIR_RENAMED
        taken = set(self._taken_by_dir.get(renamed_dir, set()))
        return self._plan_with(reference, suffix, renamed_dir, sources, taken)

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

    def execute(
        self,
        reference: str,
        suffix: str,
        output_dir: Path,
        sources: list[Path],
        move_originals: bool = False,
    ) -> list[RenameResult]:
        base_dir = Path(output_dir)
        renamed_dir = base_dir / SUBDIR_RENAMED
        os.makedirs(_extended(renamed_dir), exist_ok=True)

        taken = self._taken_by_dir.setdefault(renamed_dir, set())
        plan = self._plan_with(reference, suffix, renamed_dir, sources, taken)

        results: list[RenameResult] = []
        batch = Batch()
        for src, target_name in plan:
            dest = renamed_dir / target_name
            try:
                if not src.exists():
                    raise FileNotFoundError("le fichier source a disparu")
                _copy_exclusive(src, dest)
                batch.created.append(dest)
                if move_originals:
                    self._archive_original(src, base_dir, batch)
                results.append(RenameResult(src, dest, ok=True))
            except Exception as exc:  # noqa: BLE001
                taken.discard(collision_key(target_name))
                results.append(RenameResult(src, None, ok=False, error=str(exc)))

        if batch.created:
            self._history.append(batch)
        return results

    def _archive_original(self, src: Path, base_dir: Path, batch: Batch) -> None:
        # Best-effort : le renommage a réussi, ne pas échouer si l'archivage rate.
        try:
            done_dir = Path(base_dir) / SUBDIR_ORIGINALS
            os.makedirs(_extended(done_dir), exist_ok=True)
            moved = _unique_in_dir(done_dir, src.name)
            os.replace(_extended(src), _extended(moved))
            batch.moved.append((src, moved))
        except OSError:
            pass

    def can_undo(self) -> bool:
        return bool(self._history)

    def undo_last(self) -> UndoResult:
        if not self._history:
            return UndoResult(removed=0)

        batch = self._history[-1]
        removed = 0
        failed: list[tuple[Path, str]] = []
        remaining_created: list[Path] = []
        for path in batch.created:
            try:
                ep = _extended(path)
                if os.path.exists(ep):
                    os.unlink(ep)
                removed += 1
                self._taken_by_dir.get(path.parent, set()).discard(collision_key(path.name))
            except OSError as exc:
                failed.append((path, str(exc)))
                remaining_created.append(path)

        # On remet les originaux déplacés à leur emplacement de départ.
        remaining_moved: list[tuple[Path, Path]] = []
        for original, moved in batch.moved:
            try:
                em = _extended(moved)
                if os.path.exists(em):
                    os.makedirs(_extended(original.parent), exist_ok=True)
                    os.replace(em, _extended(original))
            except OSError as exc:
                failed.append((moved, str(exc)))
                remaining_moved.append((original, moved))

        # En cas d'échec partiel, on garde le lot (éléments restants) pour réessayer.
        if failed:
            batch.created = remaining_created
            batch.moved = remaining_moved
        else:
            self._history.pop()
        return UndoResult(removed=removed, failed=failed)
