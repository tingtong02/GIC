from __future__ import annotations

import json
from pathlib import Path
from typing import Any



def write_json_report(payload: dict[str, Any] | list[dict[str, Any]], destination: str | Path) -> Path:
    path = Path(destination)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    return path



def write_markdown_report(content: str, destination: str | Path) -> Path:
    path = Path(destination)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + '\n', encoding='utf-8')
    return path
