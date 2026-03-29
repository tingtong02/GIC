from __future__ import annotations

from pathlib import Path
from typing import Any

from gic.visualization.final_figures import bar_chart_body, write_svg


def export_failure_case_svg(failure_cases: list[dict[str, Any]], destination_root: str | Path) -> str:
    destination = Path(destination_root)
    destination.mkdir(parents=True, exist_ok=True)
    labels = [f"{item.get('event_id', '')}:{item.get('station_id', '')}" for item in failure_cases[:5]]
    values = [float(item.get('peak_timing_error_minutes') or 0.0) for item in failure_cases[:5]]
    path = destination / 'failure_cases.svg'
    write_svg(path, 920, 460, bar_chart_body(labels, values, color='#b91c1c'), title='Failure Case Peak Timing Error')
    return str(path)
