from __future__ import annotations

from pathlib import Path


class BaseLoader:
    def __init__(self, project_root: str | Path):
        self.project_root = Path(project_root).resolve()
