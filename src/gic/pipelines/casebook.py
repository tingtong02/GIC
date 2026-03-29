from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def build_final_casebook(report: dict[str, Any]) -> dict[str, Any]:
    active_eval = dict(report.get('active_eval', {}))
    case_studies = list(active_eval.get('case_studies', []))
    failure_cases = list(report.get('real_event_summary', {}).get('failure_cases', []))
    if not failure_cases:
        failure_cases = list(report.get('phase7_failure_cases', []))
    synthetic_case = case_studies[0] if case_studies else {}
    cases = [
        {
            'case_type': 'standard_success',
            'title': str(synthetic_case.get('graph_id', 'synthetic_default_case')),
            'summary': 'Synthetic broader benchmark case exported from the final default path.',
            'details': [
                f"hidden_nodes={int(synthetic_case.get('hidden_node_count', 0))}",
                f"top_error_node_count={len(synthetic_case.get('top_error_nodes', []))}",
            ],
        },
        {
            'case_type': 'real_event_validation',
            'title': str(report.get('phase7_default_promotion_decision', 'real_event_summary')),
            'summary': 'Real-event summary imported from the frozen Phase 7 report.',
            'details': [
                f"decision={report.get('phase7_default_promotion_decision', '')}",
                f"event_assets={int(report.get('real_event_summary', {}).get('event_asset_count', 0))}",
            ],
        },
        {
            'case_type': 'failure_case',
            'title': str(failure_cases[0].get('dataset_name', 'failure_case')) if failure_cases else 'failure_case',
            'summary': 'Highest-severity real-event failure retained for final boundary documentation.',
            'details': [
                f"peak_timing_error_minutes={float(failure_cases[0].get('peak_timing_error_minutes', 0.0)):.2f}" if failure_cases else 'peak_timing_error_minutes=0.00',
                f"model_id={failure_cases[0].get('model_id', '')}" if failure_cases else 'model_id=',
            ],
        },
        {
            'case_type': 'kg_view',
            'title': 'phase6_feature_only',
            'summary': 'Optional KG-enhanced final variant retained as a non-default path.',
            'details': [
                f"kg_in_default={bool(report.get('kg_in_default', False))}",
                f"phase6_hidden_mae={float(report.get('synthetic_summary', {}).get('phase6_feature_only_hidden_mae', 0.0)):.6f}",
            ],
        },
    ]
    return {
        'default_variant': report.get('default_variant', ''),
        'case_count': len(cases),
        'cases': cases,
    }
