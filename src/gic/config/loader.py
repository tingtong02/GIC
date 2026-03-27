from __future__ import annotations

import json
from pathlib import Path
from typing import Any

try:
    import yaml  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - environment dependent
    yaml = None

from .schema import ConfigValidationError, validate_config


JsonDict = dict[str, Any]


def _read_mapping(path: Path) -> JsonDict:
    text = path.read_text(encoding="utf-8")
    try:
        if yaml is not None:
            payload = yaml.safe_load(text) or {}
        else:
            payload = json.loads(text)
    except Exception as exc:  # pragma: no cover - parser branches
        raise ConfigValidationError(f"Failed to parse config file {path}: {exc}") from exc

    if not isinstance(payload, dict):
        raise ConfigValidationError(f"Config file must contain a mapping: {path}")
    return payload


def _deep_merge(base: JsonDict, override: JsonDict) -> JsonDict:
    merged: JsonDict = dict(base)
    for key, value in override.items():
        if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def _load_with_defaults(path: Path) -> JsonDict:
    raw = _read_mapping(path)
    defaults = raw.pop("defaults", [])
    if defaults is None:
        defaults = []
    if not isinstance(defaults, list):
        raise ConfigValidationError(f"Config defaults must be a list: {path}")

    merged: JsonDict = {}
    for default_entry in defaults:
        if not isinstance(default_entry, str):
            raise ConfigValidationError(f"Config default entries must be strings: {path}")
        default_path = (path.parent / default_entry).resolve()
        merged = _deep_merge(merged, _load_with_defaults(default_path))
    return _deep_merge(merged, raw)


def load_config(config_path: str | Path) -> JsonDict:
    path = Path(config_path).resolve()
    config = _load_with_defaults(path)
    validate_config(config)
    config["_meta"] = {"config_path": str(path)}
    return config


def dump_config(config: JsonDict) -> str:
    serializable = {key: value for key, value in config.items() if key != "_meta"}
    return json.dumps(serializable, indent=2, sort_keys=True)


def write_config_snapshot(config: JsonDict, destination: str | Path) -> Path:
    path = Path(destination)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dump_config(config) + "\n", encoding="utf-8")
    return path
