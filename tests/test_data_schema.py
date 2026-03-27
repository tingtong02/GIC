from __future__ import annotations

from gic.data.schema import BusRecord, GeomagneticTimeSeries, GridCase, LineRecord, to_dict


def test_grid_case_serializes_with_missing_fields() -> None:
    grid = GridCase(
        case_id="case_a",
        source_name="matpower_case118",
        case_name="case_a",
        base_mva=100.0,
        buses=[BusRecord(bus_id="bus_1", raw_bus_id="1")],
        lines=[LineRecord(line_id="line_1", raw_line_id="line_1", from_bus="bus_1", to_bus="bus_1", resistance=0.1)],
        transformers=[],
        available_fields=["base_mva"],
        missing_fields=["length_km"],
    )
    payload = to_dict(grid)
    assert payload["case_id"] == "case_a"
    assert payload["missing_fields"] == ["length_km"]


def test_geomagnetic_series_serializes() -> None:
    series = GeomagneticTimeSeries(
        series_id="geomag_a",
        source_name="sample_geomagnetic_series",
        station_id="AAA",
        time_index=["2024-01-01T00:00:00Z"],
        value_columns=["bx_nT"],
        values={"bx_nT": [1.0]},
        units={"bx_nT": "nT"},
        sampling_interval="unknown",
        timezone="UTC",
        missing_ratio=0.0,
        quality_flags=["ok"],
    )
    payload = to_dict(series)
    assert payload["station_id"] == "AAA"
    assert payload["values"]["bx_nT"] == [1.0]
