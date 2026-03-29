from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


EVIDENCE_LEVEL_DESCRIPTIONS: dict[int, str] = {
    1: 'direct_device_measurement',
    2: 'partial_local_measurement',
    3: 'event_trend_peak_reference',
    4: 'physical_plausibility_only',
}


@dataclass(slots=True)
class ValidationEvidenceBundle:
    event_id: str
    available_truth_types: list[str]
    direct_measurements: list[str]
    indirect_references: list[str]
    trend_reference: bool
    peak_reference: bool
    ranking_reference: bool
    limitations: list[str] = field(default_factory=list)
    default_level: int = 4

    def normalized_level(self) -> int:
        level = int(self.default_level)
        return min(4, max(1, level))

    def descriptor(self) -> str:
        return EVIDENCE_LEVEL_DESCRIPTIONS[self.normalized_level()]

    def applicable_metric_groups(self) -> list[str]:
        level = self.normalized_level()
        if level == 1:
            return ['proxy_numeric', 'trend', 'peak', 'ranking']
        if level == 2:
            return ['trend', 'peak', 'ranking']
        if level == 3:
            return ['trend', 'peak', 'ranking']
        return ['ranking', 'consistency']


def evidence_to_dict(value: Any) -> Any:
    if hasattr(value, '__dataclass_fields__'):
        return asdict(value)
    if isinstance(value, list):
        return [evidence_to_dict(item) for item in value]
    if isinstance(value, dict):
        return {str(key): evidence_to_dict(item) for key, item in value.items()}
    return value


def build_evidence_summary(bundles: list[ValidationEvidenceBundle]) -> dict[str, Any]:
    level_counts: dict[str, int] = {}
    for bundle in bundles:
        key = f"level_{bundle.normalized_level()}"
        level_counts[key] = level_counts.get(key, 0) + 1
    return {
        'bundle_count': len(bundles),
        'level_counts': level_counts,
        'descriptions': {f'level_{key}': value for key, value in EVIDENCE_LEVEL_DESCRIPTIONS.items()},
    }
