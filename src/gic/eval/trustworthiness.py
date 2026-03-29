from __future__ import annotations

from typing import Any



def build_trustworthiness_summary(report: dict[str, Any]) -> dict[str, Any]:
    decision = str(report.get('default_promotion_decision', 'no_real_default_promotion'))
    failure_count = int(report.get('failure_case_count', 0))
    evidence_summary = dict(report.get('evidence_summary', {}))
    lines = [
        'Real-event validation remains evidence-layered and conservative.',
        f'Default promotion decision: {decision}.',
        f'Failure cases retained: {failure_count}.',
    ]
    level_counts = evidence_summary.get('level_counts', {})
    if level_counts:
        lines.append(f'Evidence coverage by level: {level_counts}.')
    lines.append('Current conclusions should be read as real-driven validation evidence, not as full-network ground-truth accuracy.')
    return {
        'decision': decision,
        'failure_case_count': failure_count,
        'summary_lines': lines,
    }
