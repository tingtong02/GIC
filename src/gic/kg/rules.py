from __future__ import annotations

from collections import Counter
from typing import Any

from gic.graph.datasets import GraphSample


def evaluate_rule_findings(samples: list[GraphSample]) -> dict[str, Any]:
    graph_rules: dict[str, list[dict[str, Any]]] = {}
    counter: Counter[str] = Counter()
    for sample in samples:
        findings: list[dict[str, Any]] = []
        assumptions = [str(item) for item in sample.metadata.get('assumptions', [])]
        quality_flags = [str(item) for item in sample.metadata.get('quality_flags', [])]
        if assumptions:
            findings.append(
                {
                    'rule_name': 'assumption_present',
                    'severity': 'info',
                    'message': 'Sample uses filled or engineered assumptions.',
                    'evidence': assumptions,
                }
            )
            counter['assumption_present'] += 1
        if quality_flags:
            findings.append(
                {
                    'rule_name': 'quality_flags_present',
                    'severity': 'warning',
                    'message': 'Sample contains quality flags from upstream phases.',
                    'evidence': quality_flags,
                }
            )
            counter['quality_flags_present'] += 1
        if sample.metadata.get('signal_manifest_path'):
            findings.append(
                {
                    'rule_name': 'signal_context_available',
                    'severity': 'info',
                    'message': 'Sample has linked signal-ready provenance.',
                    'evidence': [str(sample.metadata['signal_manifest_path'])],
                }
            )
            counter['signal_context_available'] += 1
        if not sample.metadata.get('physics_case_path'):
            findings.append(
                {
                    'rule_name': 'missing_physics_case',
                    'severity': 'warning',
                    'message': 'Sample is missing a linked physics-ready case.',
                    'evidence': [],
                }
            )
            counter['missing_physics_case'] += 1
        graph_rules[sample.graph_id] = findings
    return {
        'graph_rules': graph_rules,
        'rule_counts': dict(counter),
        'graph_count': len(graph_rules),
    }
