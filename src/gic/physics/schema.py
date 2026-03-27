from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


PHYSICS_SCHEMA_VERSION = "1.0"


@dataclass(slots=True)
class GroundingRecord:
    bus_id: str
    grounding_resistance_ohm: float
    conductance_siemens: float
    assumed: bool = False
    notes: str = ""


@dataclass(slots=True)
class PhysicsBus:
    bus_id: str
    base_kv: float | None
    grounding: GroundingRecord
    included_in_solver: bool = True
    notes: str = ""


@dataclass(slots=True)
class PhysicsLine:
    line_id: str
    from_bus: str
    to_bus: str
    resistance_ohm: float
    length_km: float | None
    azimuth_deg: float | None
    voltage_level_kv: float | None
    included_in_solver: bool
    available_for_solver: bool
    assumptions: list[str] = field(default_factory=list)
    source_missing_fields: list[str] = field(default_factory=list)
    notes: str = ""


@dataclass(slots=True)
class PhysicsTransformer:
    transformer_id: str
    from_bus: str
    to_bus: str
    effective_resistance_ohm: float
    associated_line_id: str | None
    available_for_solver: bool
    assumptions: list[str] = field(default_factory=list)
    notes: str = ""


@dataclass(slots=True)
class PhysicsGridCase:
    case_id: str
    source_case_id: str
    buses: list[PhysicsBus]
    lines: list[PhysicsLine]
    transformers: list[PhysicsTransformer]
    grounding: list[GroundingRecord]
    gic_ready: bool
    available_for_solver: bool
    missing_required_fields: list[str]
    assumptions: list[str]
    version: str = PHYSICS_SCHEMA_VERSION


@dataclass(slots=True)
class ElectricFieldSnapshot:
    snapshot_id: str
    time: str
    field_mode: str
    reference_frame: str
    global_ex: float
    global_ey: float
    units: str
    regional_fields: dict[str, dict[str, float]] = field(default_factory=dict)
    notes: str = ""


@dataclass(slots=True)
class ElectricFieldSeries:
    series_id: str
    source_name: str
    snapshots: list[ElectricFieldSnapshot]
    notes: str = ""
    version: str = PHYSICS_SCHEMA_VERSION


@dataclass(slots=True)
class LineSolutionRecord:
    line_id: str
    projected_field: float
    induced_quantity: float
    included_in_solver: bool
    notes: str = ""


@dataclass(slots=True)
class BusSolutionRecord:
    bus_id: str
    solved_quantity: float
    connected_components_info: str
    quality_flag: str


@dataclass(slots=True)
class TransformerSolutionRecord:
    transformer_id: str
    gic_value: float
    associated_bus_ids: list[str]
    voltage_level: float | None
    quality_flag: str
    included_in_risk_output: bool


@dataclass(slots=True)
class GICSolution:
    solution_id: str
    case_id: str
    time: str
    scenario_id: str
    line_inputs: list[LineSolutionRecord]
    bus_quantities: list[BusSolutionRecord]
    transformer_gic: list[TransformerSolutionRecord]
    solver_status: str
    solver_metadata: dict[str, Any]
    assumptions: list[str]
    quality_flags: list[str]
    version: str = PHYSICS_SCHEMA_VERSION


@dataclass(slots=True)
class ScenarioConfig:
    scenario_id: str
    scenario_type: str
    case_dataset: str
    amplitude: float | None = None
    direction_deg: float | None = None
    field_units: str = "V_per_km"
    time_steps: int | None = None
    time_interval_seconds: int = 60
    timeseries_dataset: str | None = None
    parameter_perturbation: dict[str, float] = field(default_factory=dict)
    sparse_observation_ratio: float | None = None
    noise_metadata: dict[str, Any] = field(default_factory=dict)
    output_levels: list[str] = field(default_factory=lambda: ["line", "bus", "transformer"])
    assumptions: list[str] = field(default_factory=list)


@dataclass(slots=True)
class LabelManifest:
    dataset_name: str
    sample_count: int
    time_length: int
    case_source: str
    scenario_type: str
    solver_version: str
    schema_version: str
    assumptions: list[str]
    generated_at_utc: str
    paths: dict[str, str]


def physics_to_dict(value: Any) -> Any:
    if hasattr(value, "__dataclass_fields__"):
        return asdict(value)
    if isinstance(value, list):
        return [physics_to_dict(item) for item in value]
    if isinstance(value, dict):
        return {key: physics_to_dict(item) for key, item in value.items()}
    return value
