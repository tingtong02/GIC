from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def summarize_validation_results(results: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "result_count": len(results),
        "ok_count": sum(1 for item in results if item.get("ok")),
        "error_count": sum(len(item.get("errors", [])) for item in results),
        "warning_count": sum(len(item.get("warnings", [])) for item in results),
        "results": results,
    }


def write_validation_report(report: dict[str, Any], destination: str | Path) -> Path:
    path = Path(destination)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path
