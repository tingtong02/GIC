from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from gic.data.converters.id_mapping import build_id_mapping
from gic.data.schema import BusRecord, DatasetManifest, GridCase, LineRecord, TransformerRecord


def convert_matpower_to_grid_case(
    raw_case: dict[str, Any],
    *,
    dataset_name: str,
    source_name: str,
    raw_input_path: str,
) -> tuple[GridCase, DatasetManifest]:
    bus_rows = raw_case.get("bus", [])
    branch_rows = raw_case.get("branch", [])
    bus_id_map = build_id_mapping([str(int(row[0])) for row in bus_rows], "bus")

    buses = [
        BusRecord(
            bus_id=bus_id_map[str(int(row[0]))],
            raw_bus_id=str(int(row[0])),
            bus_type=int(row[1]),
            vm_pu=float(row[7]),
            va_deg=float(row[8]),
            base_kv=float(row[9]),
        )
        for row in bus_rows
    ]

    lines: list[LineRecord] = []
    transformers: list[TransformerRecord] = []
    for index, row in enumerate(branch_rows, start=1):
        raw_from = str(int(row[0]))
        raw_to = str(int(row[1]))
        line_id = f"line_{index}"
        tap_ratio = float(row[8]) if len(row) > 8 else 0.0
        series_compensated = None
        available_for_gic = row[2] is not None
        lines.append(
            LineRecord(
                line_id=line_id,
                raw_line_id=line_id,
                from_bus=bus_id_map[raw_from],
                to_bus=bus_id_map[raw_to],
                resistance=float(row[2]),
                reactance=float(row[3]) if len(row) > 3 else None,
                voltage_level_kv=None,
                series_compensated=series_compensated,
                available_for_gic=bool(available_for_gic),
                notes="length_km and azimuth_deg are not available in the Phase 1 sample fixture.",
            )
        )
        if tap_ratio not in (0.0, 1.0):
            transformers.append(
                TransformerRecord(
                    transformer_id=f"xfmr_{index}",
                    raw_transformer_id=line_id,
                    from_bus=bus_id_map[raw_from],
                    to_bus=bus_id_map[raw_to],
                    tap_ratio=tap_ratio,
                    phase_shift_deg=float(row[9]) if len(row) > 9 else None,
                    available_for_gic=False,
                    notes="Transformer inferred from non-unity tap ratio in MATPOWER branch data.",
                )
            )

    grid_case = GridCase(
        case_id=dataset_name,
        source_name=source_name,
        case_name=dataset_name,
        base_mva=float(raw_case.get("baseMVA", 0.0)),
        buses=buses,
        lines=lines,
        transformers=transformers,
        coordinate_system="unknown",
        notes="Converted from a MATPOWER-style raw case fixture during Phase 1.",
        available_fields=[
            "base_mva",
            "bus_ids",
            "line_resistance",
            "line_reactance",
            "transformer_tap_ratio",
        ],
        missing_fields=[
            "length_km",
            "azimuth_deg",
            "substations",
            "grounding_parameters",
        ],
    )
    manifest = DatasetManifest(
        dataset_name=dataset_name,
        source_name=source_name,
        generated_at_utc=datetime.now(timezone.utc).isoformat(),
        raw_input_paths=[raw_input_path],
        converter_name="convert_matpower_to_grid_case",
        schema_version=grid_case.version,
        record_count=len(buses) + len(lines) + len(transformers),
        missing_stats={"missing_fields": grid_case.missing_fields},
        notes="Grid case manifest generated in Phase 1.",
    )
    return grid_case, manifest
