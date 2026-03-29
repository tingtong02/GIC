from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from gic.config import load_config
from gic.eval.real_pipeline import build_real_event_report, export_real_event_report
from gic.reports.final_summary import build_final_report_markdown, build_final_report_payload, collect_final_versions
from gic.training import evaluate_main_model


def _resolve_path(project_root: Path, value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else (project_root / path).resolve()


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding='utf-8'))


def _assets_exist(versions: dict[str, Any]) -> dict[str, bool]:
    return {key: Path(value).exists() for key, value in dict(versions.get('assets', {})).items()}


def _active_variant(config: dict[str, Any], with_kg: bool | None) -> str:
    if with_kg is None:
        return str(config.get('final', {}).get('default_variant', 'without_kg'))
    return 'with_kg' if with_kg else 'without_kg'


def _load_frozen_reports(project_root: Path, config: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    versions = collect_final_versions(project_root, config)
    assets = dict(versions.get('assets', {}))
    phase5_report = _load_json(Path(assets['phase5_report_path']))
    phase6_report = _load_json(Path(assets['phase6_report_path']))
    phase7_report = _load_json(Path(assets['phase7_report_path']))
    return versions, phase5_report, phase6_report, phase7_report


def _evaluate_active_model(project_root: Path, config: dict[str, Any], active_variant: str, versions: dict[str, Any]) -> dict[str, Any]:
    assets = dict(versions.get('assets', {}))
    dataset_path = assets['synthetic_dataset_path']
    if active_variant == 'with_kg':
        model_config = load_config(assets['phase6_config_path'])
        checkpoint_path = assets['phase6_checkpoint_path']
    else:
        model_config = load_config(assets['phase5_config_path'])
        checkpoint_path = assets['phase5_checkpoint_path']
    evaluation = evaluate_main_model(
        config=model_config,
        dataset_path=dataset_path,
        checkpoint_path=checkpoint_path,
        split=str(config.get('final', {}).get('synthetic_split', 'test')),
        project_root=project_root,
    )
    return {
        'dataset_path': dataset_path,
        'checkpoint_path': checkpoint_path,
        'metrics': evaluation.get('metrics', {}),
        'hotspot_metrics': evaluation.get('hotspot_metrics', {}),
        'case_studies': evaluation.get('case_studies', []),
        'feature_summary': evaluation.get('feature_summary', {}),
        'kg_summary': evaluation.get('kg_summary', {}),
        'signal_summary': evaluation.get('signal_summary', {}),
    }


def _real_report(project_root: Path, config: dict[str, Any], *, refresh: bool, registry: Any = None, report_destination_root: Path | None = None) -> dict[str, Any]:
    versions = collect_final_versions(project_root, config)
    assets = dict(versions.get('assets', {}))
    phase7_report_path = Path(assets['phase7_report_path'])
    if not refresh:
        return _load_json(phase7_report_path)
    phase7_config = load_config(assets['phase7_config_path'])
    if registry is None:
        from gic.data import RegistryStore
        data_cfg = dict(phase7_config.get('data', {}))
        registry = RegistryStore(project_root=project_root, registry_root=str(data_cfg.get('registry_root', 'data/registry')))
    report = build_real_event_report(project_root=project_root, registry=registry, config=phase7_config)
    if report_destination_root is not None:
        export_real_event_report(project_root, phase7_config, report, report_destination_root)
    return report


def run_final_pipeline(
    *,
    project_root: Path,
    config: dict[str, Any],
    with_kg: bool | None = None,
    check_only: bool = False,
    refresh_real_eval: bool | None = None,
    registry: Any = None,
    report_destination_root: Path | None = None,
) -> dict[str, Any]:
    active_variant = _active_variant(config, with_kg)
    versions, phase5_report, phase6_report, phase7_report = _load_frozen_reports(project_root, config)
    assets_ok = _assets_exist(versions)
    if not all(assets_ok.values()):
        missing = [key for key, ok in assets_ok.items() if not ok]
        raise FileNotFoundError(f'Phase 8 frozen assets missing: {missing}')
    refresh = bool(config.get('final', {}).get('refresh_real_eval', False)) if refresh_real_eval is None else bool(refresh_real_eval)
    if refresh:
        phase7_report = _real_report(project_root, config, refresh=True, registry=registry, report_destination_root=report_destination_root)
    active_eval = {} if check_only else _evaluate_active_model(project_root, config, active_variant, versions)
    report = build_final_report_payload(
        project_root,
        config,
        active_variant=active_variant,
        phase5_report=phase5_report,
        phase6_report=phase6_report,
        phase7_report=phase7_report,
        active_eval=active_eval,
    )
    report['phase7_generalization_summary'] = dict(phase7_report.get('generalization_summary', {}))
    report['phase7_failure_cases'] = list(phase7_report.get('failure_cases', []))
    report['phase7_robustness_summary'] = dict(phase7_report.get('robustness_summary', {}))
    report['markdown'] = build_final_report_markdown(report)
    report['asset_check'] = assets_ok
    return report


def run_final_default(*, project_root: Path, config: dict[str, Any], check_only: bool = False, registry: Any = None, report_destination_root: Path | None = None) -> dict[str, Any]:
    return run_final_pipeline(
        project_root=project_root,
        config=config,
        with_kg=False,
        check_only=check_only,
        registry=registry,
        report_destination_root=report_destination_root,
    )
