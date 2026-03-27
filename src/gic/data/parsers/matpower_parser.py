from __future__ import annotations

import re
from pathlib import Path
from typing import Any


def _extract_scalar(text: str, key: str) -> str:
    pattern = re.compile(rf"mpc\.{re.escape(key)}\s*=\s*([^;]+);")
    match = pattern.search(text)
    if not match:
        raise ValueError(f"Missing MATPOWER scalar: {key}")
    return match.group(1).strip().strip("'")


def _extract_matrix(text: str, key: str) -> list[list[float]]:
    pattern = re.compile(rf"mpc\.{re.escape(key)}\s*=\s*\[(.*?)\];", re.DOTALL)
    match = pattern.search(text)
    if not match:
        raise ValueError(f"Missing MATPOWER matrix: {key}")
    rows: list[list[float]] = []
    for raw_line in match.group(1).splitlines():
        line = raw_line.strip()
        if not line:
            continue
        line = line.rstrip(";")
        rows.append([float(item) for item in line.split()])
    return rows


def parse_matpower_case(path: str | Path) -> dict[str, Any]:
    text = Path(path).read_text(encoding="utf-8")
    return {
        "version": _extract_scalar(text, "version"),
        "baseMVA": float(_extract_scalar(text, "baseMVA")),
        "bus": _extract_matrix(text, "bus"),
        "branch": _extract_matrix(text, "branch"),
    }
