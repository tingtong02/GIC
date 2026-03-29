from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(slots=True)
class RobustnessScenarioConfig:
    sensor_dropout: list[float] = field(default_factory=list)
    timing_shift_minutes: list[int] = field(default_factory=list)
    noise_stress_std: list[float] = field(default_factory=list)



def build_robustness_summary(rows: list[dict[str, Any]], scenario: RobustnessScenarioConfig) -> dict[str, Any]:
    return {
        'scenario': asdict(scenario),
        'row_count': len(rows),
        'rows': rows,
    }
