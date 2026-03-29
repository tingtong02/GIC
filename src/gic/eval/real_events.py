from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from gic.eval.evidence import ValidationEvidenceBundle, evidence_to_dict
from gic.eval.reporting import write_json_report


@dataclass(slots=True)
class RealEventRecord:
    event_id: str
    event_name: str
    time_range: str
    data_sources: list[str]
    available_geomagnetic_inputs: list[str]
    available_geoelectric_inputs: list[str]
    available_gic_observations: list[str]
    quality_notes: list[str]
    region: str
    status: str
    evidence: ValidationEvidenceBundle


@dataclass(slots=True)
class RealEventDataset:
    event_set_name: str
    records: list[RealEventRecord]
    notes: str = ''


@dataclass(slots=True)
class RealEventManifest:
    event_set_name: str
    record_count: int
    generated_at_utc: str
    records: list[dict[str, Any]]
    paths: dict[str, str] = field(default_factory=dict)
    notes: str = ''


@dataclass(slots=True)
class RealEventAsset:
    event_id: str
    dataset_name: str
    station_id: str
    time_range: str
    evidence_level: int
    interim_timeseries_path: str
    interim_manifest_path: str
    signal_manifest_path: str | None
    signal_comparison_path: str | None
    physics_solution_path: str | None
    graph_dataset_path: str | None
    notes: list[str] = field(default_factory=list)


@dataclass(slots=True)
class RealEventBuildResult:
    dataset: RealEventDataset
    manifest: RealEventManifest
    assets: list[RealEventAsset]



def real_event_to_dict(value: Any) -> Any:
    if hasattr(value, '__dataclass_fields__'):
        return asdict(value)
    if isinstance(value, list):
        return [real_event_to_dict(item) for item in value]
    if isinstance(value, dict):
        return {str(key): real_event_to_dict(item) for key, item in value.items()}
    return value



def export_real_event_manifest(result: RealEventBuildResult, destination: str | Path) -> Path:
    payload = {
        'event_set_name': result.manifest.event_set_name,
        'record_count': result.manifest.record_count,
        'generated_at_utc': result.manifest.generated_at_utc,
        'records': real_event_to_dict(result.dataset.records),
        'assets': real_event_to_dict(result.assets),
        'notes': result.manifest.notes,
    }
    return write_json_report(payload, destination)



def flatten_event_records(event_payload: dict[str, Any]) -> RealEventDataset:
    notes = str(event_payload.get('notes', ''))
    event_set_name = str(event_payload.get('event_set_name', 'real_event_set'))
    raw_records: list[dict[str, Any]] = []
    if isinstance(event_payload.get('events'), list):
        raw_records.extend([dict(item) for item in event_payload.get('events', []) if isinstance(item, dict)])
    groups = event_payload.get('groups', {})
    if isinstance(groups, dict):
        for _, items in groups.items():
            if isinstance(items, list):
                raw_records.extend([dict(item) for item in items if isinstance(item, dict)])
    records: list[RealEventRecord] = []
    for item in raw_records:
        evidence_payload = dict(item.get('evidence', {}))
        records.append(
            RealEventRecord(
                event_id=str(item.get('event_id', '')),
                event_name=str(item.get('event_name', '')),
                time_range=str(item.get('time_range', '')),
                data_sources=[str(value) for value in item.get('data_sources', [])],
                available_geomagnetic_inputs=[str(value) for value in item.get('available_geomagnetic_inputs', [])],
                available_geoelectric_inputs=[str(value) for value in item.get('available_geoelectric_inputs', [])],
                available_gic_observations=[str(value) for value in item.get('available_gic_observations', [])],
                quality_notes=[str(value) for value in item.get('quality_notes', [])],
                region=str(item.get('region', 'unknown')),
                status=str(item.get('status', 'active')),
                evidence=ValidationEvidenceBundle(
                    event_id=str(item.get('event_id', '')),
                    available_truth_types=[str(value) for value in evidence_payload.get('available_truth_types', [])],
                    direct_measurements=[str(value) for value in evidence_payload.get('direct_measurements', [])],
                    indirect_references=[str(value) for value in evidence_payload.get('indirect_references', [])],
                    trend_reference=bool(evidence_payload.get('trend_reference', False)),
                    peak_reference=bool(evidence_payload.get('peak_reference', False)),
                    ranking_reference=bool(evidence_payload.get('ranking_reference', False)),
                    limitations=[str(value) for value in evidence_payload.get('limitations', [])],
                    default_level=int(evidence_payload.get('default_level', 4)),
                ),
            )
        )
    return RealEventDataset(event_set_name=event_set_name, records=records, notes=notes)
