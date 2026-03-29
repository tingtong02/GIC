from __future__ import annotations

from typing import Any



def build_phase7_report_markdown(report: dict[str, Any]) -> str:
    sections = [
        '# Phase 7 Real Event Validation Report',
        '',
        '## Summary',
        f"- Event set: `{report.get('event_set_name', '')}`",
        f"- Event asset count: `{report.get('event_asset_count', 0)}`",
        f"- Model rows: `{report.get('result_row_count', 0)}`",
        f"- Failure cases: `{report.get('failure_case_count', 0)}`",
        '',
        '## Default Decision',
        f"- `{report.get('default_promotion_decision', 'no_real_default_promotion')}`",
        '',
        '## Evidence Summary',
        f"- `{report.get('evidence_summary', {})}`",
        '',
        '## Generalization Summary',
        f"- `{report.get('generalization_summary', {})}`",
        '',
        '## Robustness Summary',
        f"- `{report.get('robustness_summary', {})}`",
        '',
        '## Trustworthiness',
    ]
    for line in report.get('trustworthiness_summary', {}).get('summary_lines', []):
        sections.append(f'- {line}')
    return '\n'.join(sections).rstrip() + '\n'
