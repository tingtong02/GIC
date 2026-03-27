from __future__ import annotations

from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

from gic.data.registry import RegistryStore
from gic.data.schema import GeomagneticTimeSeries, GridCase


def validate_grid_case(grid_case: GridCase) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    bus_ids = [bus.bus_id for bus in grid_case.buses]
    if len(bus_ids) != len(set(bus_ids)):
        errors.append("Bus ids must be unique")

    line_ids = [line.line_id for line in grid_case.lines]
    if len(line_ids) != len(set(line_ids)):
        errors.append("Line ids must be unique")

    known_buses = set(bus_ids)
    connected_buses: set[str] = set()
    for line in grid_case.lines:
        if line.from_bus not in known_buses or line.to_bus not in known_buses:
            errors.append(f"Line {line.line_id} references unknown bus")
        connected_buses.add(line.from_bus)
        connected_buses.add(line.to_bus)
    isolated = sorted(known_buses - connected_buses)
    if isolated:
        warnings.append(f"Isolated buses detected: {', '.join(isolated)}")
    if grid_case.missing_fields:
        warnings.append(f"Missing fields recorded: {', '.join(grid_case.missing_fields)}")

    return {
        "asset_type": "grid_case",
        "asset_id": grid_case.case_id,
        "ok": not errors,
        "errors": errors,
        "warnings": warnings,
        "stats": {
            "bus_count": len(grid_case.buses),
            "line_count": len(grid_case.lines),
            "transformer_count": len(grid_case.transformers),
        },
    }


def validate_geomagnetic_timeseries(series: GeomagneticTimeSeries) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    parsed = [datetime.fromisoformat(item.replace("Z", "+00:00")) for item in series.time_index]
    if parsed != sorted(parsed):
        errors.append("Time index must be monotonic")
    counts = Counter(series.time_index)
    duplicates = [stamp for stamp, count in counts.items() if count > 1]
    if duplicates:
        errors.append(f"Duplicate timestamps detected: {duplicates}")
    if series.missing_ratio > 0.2:
        warnings.append(f"Missing ratio is high: {series.missing_ratio:.3f}")
    if series.sampling_interval == "unknown":
        warnings.append("Sampling interval could not be inferred")
    for column, values in series.values.items():
        if all(value is None for value in values):
            errors.append(f"Column {column} has no valid numeric values")

    return {
        "asset_type": "geomagnetic_timeseries",
        "asset_id": series.series_id,
        "ok": not errors,
        "errors": errors,
        "warnings": warnings,
        "stats": {
            "points": len(series.time_index),
            "value_columns": list(series.value_columns),
            "missing_ratio": series.missing_ratio,
        },
    }


def validate_registry_consistency(registry: RegistryStore) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    dataset_names = [dataset.dataset_name for dataset in registry.list_datasets()]
    if len(dataset_names) != len(set(dataset_names)):
        errors.append("Dataset names in registry must be unique")

    for dataset in registry.list_datasets():
        if not dataset.schema_version:
            errors.append(f"Dataset {dataset.dataset_name} is missing schema_version")
        dataset_path = registry.resolve_dataset_path(dataset.dataset_name)
        if not dataset_path.exists():
            errors.append(f"Dataset path does not exist: {dataset.relative_path}")
        try:
            registry.get_source(dataset.source_name)
        except Exception:
            errors.append(f"Dataset {dataset.dataset_name} references unknown source {dataset.source_name}")

    for source in registry.list_sources():
        if not source.purpose:
            warnings.append(f"Source {source.source_name} is missing purpose")

    return {
        "asset_type": "registry",
        "asset_id": "data_registry",
        "ok": not errors,
        "errors": errors,
        "warnings": warnings,
        "stats": {
            "source_count": len(registry.list_sources()),
            "dataset_count": len(registry.list_datasets()),
            "active_dataset_count": len(registry.active_datasets()),
        },
    }


def validation_output_path(project_root: Path, relative_root: str, name: str) -> Path:
    return (project_root / relative_root / name).resolve()
