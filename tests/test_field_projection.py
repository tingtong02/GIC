from __future__ import annotations

from gic.physics.projections import induced_voltage, project_field_onto_line


def test_project_field_onto_line() -> None:
    assert round(project_field_onto_line(1.0, 0.0, 0.0), 6) == 1.0
    assert round(project_field_onto_line(1.0, 0.0, 90.0), 6) == 0.0


def test_induced_voltage() -> None:
    assert induced_voltage(2.0, 10.0) == 20.0
