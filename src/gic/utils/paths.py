from __future__ import annotations

from pathlib import Path


def resolve_project_root(project_root: str | Path | None = None) -> Path:
    root = Path(project_root) if project_root is not None else Path.cwd()
    return root.resolve()


def resolve_path(project_root: Path, value: str | Path) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return (project_root / path).resolve()


def ensure_directory(path: str | Path) -> Path:
    directory = Path(path)
    directory.mkdir(parents=True, exist_ok=True)
    return directory
