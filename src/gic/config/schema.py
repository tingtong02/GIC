from __future__ import annotations

from collections.abc import Mapping
from typing import Any


class ConfigValidationError(ValueError):
    """Raised when the project configuration is incomplete or malformed."""


def _require_mapping(config: Mapping[str, Any], path: tuple[str, ...]) -> Any:
    current: Any = config
    visited: list[str] = []
    for key in path:
        visited.append(key)
        if not isinstance(current, Mapping) or key not in current:
            dotted = ".".join(visited)
            raise ConfigValidationError(f"Missing required config field: {dotted}")
        current = current[key]
    return current


def validate_config(config: Mapping[str, Any]) -> None:
    if not isinstance(config, Mapping):
        raise ConfigValidationError("Configuration payload must be a mapping")

    required_paths = [
        ("project", "name"),
        ("project", "stage"),
        ("runtime", "mode"),
        ("logging", "level"),
        ("paths", "artifacts_root"),
        ("paths", "logs_root"),
        ("paths", "reports_root"),
        ("paths", "config_snapshot_name"),
        ("paths", "metadata_name"),
        ("paths", "summary_name"),
        ("paths", "log_filename"),
    ]

    for path in required_paths:
        value = _require_mapping(config, path)
        if isinstance(value, str) and not value.strip():
            dotted = ".".join(path)
            raise ConfigValidationError(f"Config field must not be empty: {dotted}")
