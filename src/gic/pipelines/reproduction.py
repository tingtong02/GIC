from __future__ import annotations

from pathlib import Path
from typing import Any

from gic.pipelines.casebook import build_final_casebook
from gic.pipelines.final_pipeline import run_final_pipeline
from gic.pipelines.visualization import build_final_visuals
from gic.reports.final_exports import export_final_casebook, export_final_doc_summary, export_final_report_bundle


def run_final_reproduction(
    *,
    project_root: Path,
    config: dict[str, Any],
    destination_root: Path,
    with_kg: bool | None = None,
    check_only: bool = False,
    registry: Any = None,
    phase6_report: dict[str, Any],
    phase7_report: dict[str, Any],
) -> dict[str, Any]:
    report = run_final_pipeline(
        project_root=project_root,
        config=config,
        with_kg=with_kg,
        check_only=check_only,
        registry=registry,
        report_destination_root=destination_root,
    )
    report['phase7_generalization_summary'] = dict(phase7_report.get('generalization_summary', {}))
    report['phase7_failure_cases'] = list(phase7_report.get('failure_cases', []))
    report['phase7_robustness_summary'] = dict(phase7_report.get('robustness_summary', {}))
    summary_paths = export_final_report_bundle(report, destination_root=destination_root, summary_name='final_summary')
    visual_paths = build_final_visuals(
        report,
        destination_root=destination_root / 'visuals',
        phase6_report=phase6_report,
        phase7_report=phase7_report,
    )
    casebook = build_final_casebook(report)
    casebook_paths = export_final_casebook(
        casebook,
        destination_root=destination_root,
        json_name='final_casebook.json',
        md_name='final_casebook.md',
    )
    doc_summary = (
        '# Final Doc Summary\n\n'
        '- Final reproduction completed.\n'
        f"- Default variant is `{report.get('default_variant', '')}`.\n"
    )
    doc_summary_path = export_final_doc_summary(doc_summary, destination_root=destination_root, filename='final_doc_summary.md')
    return {
        'report': report,
        'summary_paths': summary_paths,
        'visual_paths': visual_paths,
        'casebook_paths': casebook_paths,
        'doc_summary_path': doc_summary_path,
    }
