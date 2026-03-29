from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from gic.visualization import (
    export_failure_case_svg,
    export_kg_view_svg,
    export_model_comparison_svgs,
    export_network_map_svg,
    export_timeline_svg,
)


def build_final_visuals(report: dict[str, Any], *, destination_root: Path, phase6_report: dict[str, Any], phase7_report: dict[str, Any]) -> dict[str, str]:
    destination_root.mkdir(parents=True, exist_ok=True)
    outputs: dict[str, str] = {}
    outputs.update(export_model_comparison_svgs(report, destination_root))
    outputs['network_map_svg'] = export_network_map_svg(dict(report.get('active_eval', {})), destination_root)
    outputs['timeline_svg'] = export_timeline_svg(dict(phase7_report.get('generalization_summary', {})), destination_root)
    outputs['failure_cases_svg'] = export_failure_case_svg(list(phase7_report.get('failure_cases', [])), destination_root)
    outputs['kg_view_svg'] = export_kg_view_svg(phase6_report, destination_root)
    index_path = destination_root / 'visual_manifest.json'
    index_path.write_text(json.dumps(outputs, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    outputs['visual_manifest_path'] = str(index_path)
    return outputs
