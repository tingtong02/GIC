from __future__ import annotations

import argparse
import json
import os
import platform
import sys
from pathlib import Path
from typing import Any

from gic.config import dump_config, load_config
from gic.data import RegistryStore, to_dict
from gic.data.converters.grid_to_physics import convert_grid_case_to_physics
from gic.data.loaders.matpower_loader import MatpowerLoader
from gic.data.loaders.timeseries_loader import TimeSeriesLoader
from gic.data.validation.checks import (
    validate_geomagnetic_timeseries,
    validate_grid_case,
    validate_registry_consistency,
)
from gic.data.validation.reports import summarize_validation_results, write_validation_report
from gic.physics.export import export_label_bundle
from gic.physics.field import build_series_from_timeseries, uniform_field_from_scenario
from gic.physics.postprocess import summarize_solution
from gic.physics.scenarios import generate_scenarios
from gic.physics.solver import solve_series, solve_snapshot
from gic.physics.validation import validate_physics_case, validate_solution
from gic.signal import (
    FrontendConfig,
    build_comparison_report,
    build_frontend,
    build_signal_sample_from_timeseries,
    export_comparison_report,
    export_frontend_result,
    signal_to_dict,
    validate_frontend_result,
    validate_signal_sample,
)
from gic.graph import (
    build_graph_samples_from_config,
    build_split_assignments,
    export_graph_dataset,
    export_graph_samples,
    load_graph_manifest,
    validate_graph_manifest,
    validate_graph_sample,
)
from gic.eval import (
    build_phase5_report_markdown,
    compare_metric_rows,
    compare_with_phase4_report,
    write_json_report,
    write_markdown_report,
)
from gic.training import (
    evaluate_baseline_model,
    evaluate_main_model,
    run_phase5_ablation_suite,
    train_baseline_model,
    train_main_model,
)
from gic.utils.logging_utils import configure_logger
from gic.utils.paths import ensure_directory, resolve_project_root
from gic.utils.runtime import initialize_run, write_summary

DEFAULT_CONFIG = "configs/phase0/phase0_dev.yaml"
DEFAULT_PHASE1_CONFIG = "configs/phase1/phase1_dev.yaml"
DEFAULT_PHASE2_CONFIG = "configs/phase2/phase2_dev.yaml"
DEFAULT_PHASE3_CONFIG = "configs/phase3/phase3_dev.yaml"
DEFAULT_PHASE4_CONFIG = "configs/phase4/phase4_dev.yaml"
DEFAULT_PHASE5_CONFIG = "configs/phase5/phase5_dev.yaml"


def _common_run_parser(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--config", default=DEFAULT_CONFIG, help="Path to the config file")
    parser.add_argument(
        "--project-root",
        default=None,
        help="Optional project root override for writing artifacts, logs, reports, and data outputs",
    )


def _common_data_parser(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--config", default=DEFAULT_PHASE1_CONFIG, help="Path to the Phase 1 config file")
    parser.add_argument(
        "--project-root",
        default=None,
        help="Optional project root override for registry and output resolution",
    )
    parser.add_argument("--dataset-name", default=None, help="Optional dataset name override")


def _common_physics_parser(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--config", default=DEFAULT_PHASE2_CONFIG, help="Path to the Phase 2 config file")
    parser.add_argument(
        "--project-root",
        default=None,
        help="Optional project root override for registry, processed outputs, and reports",
    )
    parser.add_argument("--scenario-mode", default=None, help="Optional scenario mode override")


def _common_signal_parser(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--config", default=DEFAULT_PHASE3_CONFIG, help="Path to the Phase 3 config file")
    parser.add_argument(
        "--project-root",
        default=None,
        help="Optional project root override for registry, processed outputs, and reports",
    )
    parser.add_argument("--dataset-name", default=None, help="Optional Phase 3 dataset override")
    parser.add_argument("--method", default=None, help="Optional frontend method override")


def _common_graph_parser(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--config", default=DEFAULT_PHASE4_CONFIG, help="Path to the Phase 4 config file")
    parser.add_argument(
        "--project-root",
        default=None,
        help="Optional project root override for graph-ready outputs and reports",
    )


def _common_baseline_parser(parser: argparse.ArgumentParser) -> None:
    _common_graph_parser(parser)
    parser.add_argument("--model-type", default="mlp", help="Baseline model type")
    parser.add_argument("--dataset-path", default=None, help="Optional graph-ready dataset override")


def _common_main_model_parser(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--config", default=DEFAULT_PHASE5_CONFIG, help="Path to the Phase 5 config file")
    parser.add_argument(
        "--project-root",
        default=None,
        help="Optional project root override for Phase 5 artifacts, reports, and dataset resolution",
    )
    parser.add_argument("--dataset-path", default=None, help="Optional Phase 5 graph-ready dataset override")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="gic")
    subparsers = parser.add_subparsers(dest="command", required=True)

    show_config = subparsers.add_parser("show-config", help="Print the resolved configuration")
    show_config.add_argument("--config", default=DEFAULT_CONFIG, help="Path to the config file")
    show_config.set_defaults(func=cmd_show_config)

    init_run = subparsers.add_parser("init-run", help="Create run directories and metadata")
    _common_run_parser(init_run)
    init_run.set_defaults(func=cmd_init_run)

    run_cmd = subparsers.add_parser("run", help="Execute the Phase 0 dry run")
    _common_run_parser(run_cmd)
    run_cmd.set_defaults(func=cmd_run)

    validate_env = subparsers.add_parser("validate-env", help="Print a lightweight env summary")
    validate_env.set_defaults(func=cmd_validate_env)

    data_list_sources = subparsers.add_parser("data-list-sources", help="List registered data sources")
    _common_data_parser(data_list_sources)
    data_list_sources.set_defaults(func=cmd_data_list_sources)

    data_list_datasets = subparsers.add_parser("data-list-datasets", help="List registered datasets")
    _common_data_parser(data_list_datasets)
    data_list_datasets.set_defaults(func=cmd_data_list_datasets)

    data_validate = subparsers.add_parser("data-validate", help="Validate registry and active datasets")
    _common_data_parser(data_validate)
    data_validate.set_defaults(func=cmd_data_validate)

    data_build_manifest = subparsers.add_parser("data-build-manifest", help="Build a manifest for a dataset")
    _common_data_parser(data_build_manifest)
    data_build_manifest.set_defaults(func=cmd_data_build_manifest)

    data_convert_sample = subparsers.add_parser("data-convert-sample", help="Convert active sample datasets")
    _common_data_parser(data_convert_sample)
    data_convert_sample.set_defaults(func=cmd_data_convert_sample)

    physics_build_case = subparsers.add_parser("physics-build-case", help="Build a PhysicsGridCase from a GridCase")
    _common_physics_parser(physics_build_case)
    physics_build_case.set_defaults(func=cmd_physics_build_case)

    physics_solve_snapshot = subparsers.add_parser("physics-solve-snapshot", help="Solve a single uniform field snapshot")
    _common_physics_parser(physics_solve_snapshot)
    physics_solve_snapshot.set_defaults(func=cmd_physics_solve_snapshot)

    physics_solve_series = subparsers.add_parser("physics-solve-series", help="Solve a time-series field scenario")
    _common_physics_parser(physics_solve_series)
    physics_solve_series.set_defaults(func=cmd_physics_solve_series)

    physics_generate_scenarios = subparsers.add_parser("physics-generate-scenarios", help="Generate scenario metadata")
    _common_physics_parser(physics_generate_scenarios)
    physics_generate_scenarios.set_defaults(func=cmd_physics_generate_scenarios)

    physics_export_labels = subparsers.add_parser("physics-export-labels", help="Export labels for configured physics scenarios")
    _common_physics_parser(physics_export_labels)
    physics_export_labels.set_defaults(func=cmd_physics_export_labels)

    physics_validate_solution = subparsers.add_parser("physics-validate-solution", help="Run physics sanity checks")
    _common_physics_parser(physics_validate_solution)
    physics_validate_solution.set_defaults(func=cmd_physics_validate_solution)

    signal_run_frontend = subparsers.add_parser("signal-run-frontend", help="Run one Phase 3 frontend method")
    _common_signal_parser(signal_run_frontend)
    signal_run_frontend.set_defaults(func=cmd_signal_run_frontend)

    signal_compare_frontends = subparsers.add_parser("signal-compare-frontends", help="Compare active Phase 3 frontend methods")
    _common_signal_parser(signal_compare_frontends)
    signal_compare_frontends.set_defaults(func=cmd_signal_compare_frontends)

    signal_export_features = subparsers.add_parser("signal-export-features", help="Export signal-ready assets for Phase 3 methods")
    _common_signal_parser(signal_export_features)
    signal_export_features.set_defaults(func=cmd_signal_export_features)

    signal_validate_input = subparsers.add_parser("signal-validate-input", help="Validate Phase 3 signal input preparation")
    _common_signal_parser(signal_validate_input)
    signal_validate_input.set_defaults(func=cmd_signal_validate_input)

    signal_build_report = subparsers.add_parser("signal-build-report", help="Build a Phase 3 comparison report")
    _common_signal_parser(signal_build_report)
    signal_build_report.set_defaults(func=cmd_signal_build_report)

    graph_build_samples = subparsers.add_parser("graph-build-samples", help="Build and validate Phase 4 graph samples")
    _common_graph_parser(graph_build_samples)
    graph_build_samples.set_defaults(func=cmd_graph_build_samples)

    graph_export_dataset = subparsers.add_parser("graph-export-dataset", help="Export Phase 4 graph-ready samples and dataset manifest")
    _common_graph_parser(graph_export_dataset)
    graph_export_dataset.set_defaults(func=cmd_graph_export_dataset)

    graph_build_report = subparsers.add_parser("graph-build-report", help="Build a Phase 4 graph-ready summary report")
    _common_graph_parser(graph_build_report)
    graph_build_report.set_defaults(func=cmd_graph_build_report)

    train_baseline = subparsers.add_parser("train-baseline", help="Train a Phase 4 baseline model")
    _common_baseline_parser(train_baseline)
    train_baseline.add_argument("--epochs", type=int, default=None, help="Optional epoch override for the current run")
    train_baseline.set_defaults(func=cmd_train_baseline)

    eval_baseline = subparsers.add_parser("eval-baseline", help="Evaluate a Phase 4 baseline checkpoint")
    _common_baseline_parser(eval_baseline)
    eval_baseline.add_argument("--checkpoint", default=None, help="Path to a trained checkpoint")
    eval_baseline.add_argument("--split", default="test", help="Dataset split to evaluate")
    eval_baseline.set_defaults(func=cmd_eval_baseline)

    train_main_model_parser = subparsers.add_parser("train-main-model", help="Train the Phase 5 main model")
    _common_main_model_parser(train_main_model_parser)
    train_main_model_parser.add_argument("--epochs", type=int, default=None, help="Optional epoch override for the current run")
    train_main_model_parser.set_defaults(func=cmd_train_main_model)

    eval_main_model_parser = subparsers.add_parser("eval-main-model", help="Evaluate a Phase 5 main-model checkpoint")
    _common_main_model_parser(eval_main_model_parser)
    eval_main_model_parser.add_argument("--checkpoint", default=None, help="Path to a trained Phase 5 checkpoint")
    eval_main_model_parser.add_argument("--split", default=None, help="Dataset split to evaluate")
    eval_main_model_parser.set_defaults(func=cmd_eval_main_model)

    export_main_predictions = subparsers.add_parser("export-main-predictions", help="Export Phase 5 sample-level predictions")
    _common_main_model_parser(export_main_predictions)
    export_main_predictions.add_argument("--checkpoint", default=None, help="Path to a trained Phase 5 checkpoint")
    export_main_predictions.add_argument("--split", default=None, help="Dataset split to export")
    export_main_predictions.set_defaults(func=cmd_export_main_predictions)

    run_ablation = subparsers.add_parser("run-ablation", help="Run Phase 5 ablations")
    _common_main_model_parser(run_ablation)
    run_ablation.set_defaults(func=cmd_run_ablation)

    build_main_report = subparsers.add_parser("build-main-report", help="Build the Phase 5 main-model report")
    _common_main_model_parser(build_main_report)
    build_main_report.set_defaults(func=cmd_build_main_report)

    return parser


def _serialize_result(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, indent=2, sort_keys=True))


def _load_phase1_context(args: argparse.Namespace) -> tuple[dict[str, Any], Path, RegistryStore]:
    config = load_config(args.config)
    project_root = resolve_project_root(args.project_root)
    data_cfg = config.get("data")
    if not isinstance(data_cfg, dict):
        raise ValueError("Phase 1 config requires a data section")
    registry_root = data_cfg.get("registry_root")
    if not isinstance(registry_root, str) or not registry_root:
        raise ValueError("Phase 1 config requires data.registry_root")
    registry = RegistryStore(project_root=project_root, registry_root=registry_root)
    return config, project_root, registry


def _load_phase2_context(args: argparse.Namespace) -> tuple[dict[str, Any], Path, RegistryStore]:
    config = load_config(args.config)
    project_root = resolve_project_root(args.project_root)
    data_cfg = config.get("data")
    if not isinstance(data_cfg, dict):
        raise ValueError("Phase 2 config requires a data section")
    registry_root = data_cfg.get("registry_root")
    if not isinstance(registry_root, str) or not registry_root:
        raise ValueError("Phase 2 config requires data.registry_root")
    registry = RegistryStore(project_root=project_root, registry_root=registry_root)
    return config, project_root, registry


def _load_phase3_context(args: argparse.Namespace) -> tuple[dict[str, Any], Path, RegistryStore]:
    config = load_config(args.config)
    project_root = resolve_project_root(args.project_root)
    data_cfg = config.get("data")
    if not isinstance(data_cfg, dict):
        raise ValueError("Phase 3 config requires a data section")
    registry_root = data_cfg.get("registry_root")
    if not isinstance(registry_root, str) or not registry_root:
        raise ValueError("Phase 3 config requires data.registry_root")
    registry = RegistryStore(project_root=project_root, registry_root=registry_root)
    return config, project_root, registry


def _load_phase4_context(args: argparse.Namespace) -> tuple[dict[str, Any], Path]:
    config = load_config(args.config)
    project_root = resolve_project_root(args.project_root)
    data_cfg = config.get("data")
    if not isinstance(data_cfg, dict):
        raise ValueError("Phase 4 config requires a data section")
    registry_root = data_cfg.get("registry_root")
    if not isinstance(registry_root, str) or not registry_root:
        raise ValueError("Phase 4 config requires data.registry_root")
    return config, project_root


def _load_phase5_context(args: argparse.Namespace) -> tuple[dict[str, Any], Path]:
    config = load_config(args.config)
    project_root = resolve_project_root(args.project_root)
    data_cfg = config.get("data")
    if not isinstance(data_cfg, dict):
        raise ValueError("Phase 5 config requires a data section")
    registry_root = data_cfg.get("registry_root")
    if not isinstance(registry_root, str) or not registry_root:
        raise ValueError("Phase 5 config requires data.registry_root")
    return config, project_root


def _convert_dataset(
    *,
    project_root: Path,
    config: dict[str, Any],
    registry: RegistryStore,
    dataset_name: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    dataset = registry.get_dataset(dataset_name)
    source = registry.get_source(dataset.source_name)
    interim_root = project_root / config["data"]["interim_root"]
    if source.source_type == "grid_case":
        asset, manifest = MatpowerLoader(project_root).load(dataset, source)
        output_dir = ensure_directory(interim_root / "grid_cases")
        output_path = output_dir / f"{dataset.dataset_name}.json"
    elif source.source_type == "geomagnetic_timeseries":
        asset, manifest = TimeSeriesLoader(project_root).load_geomagnetic(dataset, source)
        output_dir = ensure_directory(interim_root / "timeseries")
        output_path = output_dir / f"{dataset.dataset_name}.json"
    else:
        raise ValueError(f"Unsupported source type for conversion: {source.source_type}")

    output_path.write_text(json.dumps(to_dict(asset), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    manifest_path = output_dir / f"{dataset.dataset_name}.manifest.json"
    if config["data"]["conversion"].get("write_manifest", True):
        manifest_path.write_text(json.dumps(to_dict(manifest), indent=2, sort_keys=True) + "\n", encoding="utf-8")

    payload = {
        "dataset_name": dataset.dataset_name,
        "source_name": source.source_name,
        "source_type": source.source_type,
        "output_path": str(output_path),
        "manifest_path": str(manifest_path),
    }
    return payload, to_dict(manifest)


def _validate_active_assets(project_root: Path, registry: RegistryStore) -> list[dict[str, Any]]:
    results = [validate_registry_consistency(registry)]
    for dataset in registry.active_datasets():
        source = registry.get_source(dataset.source_name)
        if source.source_type == "grid_case":
            asset, _ = MatpowerLoader(project_root).load(dataset, source)
            results.append(validate_grid_case(asset))
        elif source.source_type == "geomagnetic_timeseries":
            asset, _ = TimeSeriesLoader(project_root).load_geomagnetic(dataset, source)
            results.append(validate_geomagnetic_timeseries(asset))
    return results


def _load_grid_case_from_registry(project_root: Path, registry: RegistryStore, dataset_name: str):
    dataset = registry.get_dataset(dataset_name)
    source = registry.get_source(dataset.source_name)
    return MatpowerLoader(project_root).load(dataset, source)


def _load_geomagnetic_series_from_registry(project_root: Path, registry: RegistryStore, dataset_name: str):
    dataset = registry.get_dataset(dataset_name)
    source = registry.get_source(dataset.source_name)
    return TimeSeriesLoader(project_root).load_geomagnetic(dataset, source)


def _solve_physics_mode(
    *,
    config: dict[str, Any],
    project_root: Path,
    registry: RegistryStore,
    scenario_mode: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    scenarios = generate_scenarios(config, scenario_mode)
    outputs: list[dict[str, Any]] = []
    reports: list[dict[str, Any]] = []
    for scenario in scenarios:
        grid_case, _ = _load_grid_case_from_registry(project_root, registry, scenario.case_dataset)
        physics_case = convert_grid_case_to_physics(grid_case, config["physics"])
        physics_case_report = validate_physics_case(physics_case)

        if scenario.scenario_type == "timeseries_field":
            if not scenario.timeseries_dataset:
                raise ValueError("timeseries_field scenario requires timeseries_dataset")
            series, _ = _load_geomagnetic_series_from_registry(project_root, registry, scenario.timeseries_dataset)
            field_series = build_series_from_timeseries(
                scenario,
                series,
                float(config["physics"]["field"].get("geomagnetic_scale_v_per_km_per_nt", 0.01)),
            )
            solutions = solve_series(physics_case, field_series, scenario.scenario_id)
        else:
            snapshot = uniform_field_from_scenario(scenario)
            solutions = [solve_snapshot(physics_case, snapshot, scenario.scenario_id)]

        solution_reports = [validate_solution(item) for item in solutions]
        exported_paths = export_label_bundle(
            project_root=project_root,
            outputs_config=config["physics"]["outputs"],
            scenario=scenario,
            solutions=solutions,
        )
        outputs.append(
            {
                "scenario_id": scenario.scenario_id,
                "scenario_type": scenario.scenario_type,
                "solution_count": len(solutions),
                "exported_paths": exported_paths,
                "solution_summaries": [summarize_solution(item) for item in solutions],
            }
        )
        reports.append(
            {
                "scenario_id": scenario.scenario_id,
                "physics_case": physics_case_report,
                "solutions": solution_reports,
            }
        )
    return outputs, reports


def _phase3_dataset_name(args: argparse.Namespace, config: dict[str, Any]) -> str:
    signal_cfg = config.get("signal")
    if not isinstance(signal_cfg, dict):
        raise ValueError("Phase 3 config requires a signal section")
    dataset_name = args.dataset_name or signal_cfg.get("input_dataset")
    if not isinstance(dataset_name, str) or not dataset_name:
        raise ValueError("Phase 3 requires signal.input_dataset or --dataset-name")
    return dataset_name


def _build_phase3_frontend_config(config: dict[str, Any], method_name: str) -> FrontendConfig:
    signal_cfg = config.get("signal")
    if not isinstance(signal_cfg, dict):
        raise ValueError("Phase 3 config requires a signal section")
    methods_cfg = signal_cfg.get("methods")
    if not isinstance(methods_cfg, dict) or method_name not in methods_cfg:
        raise ValueError(f"Phase 3 config missing method configuration for {method_name}")
    method_cfg = methods_cfg[method_name]
    if not isinstance(method_cfg, dict):
        raise ValueError(f"Method config must be a mapping: {method_name}")
    parameters = method_cfg.get("parameters", {})
    if not isinstance(parameters, dict):
        raise ValueError(f"Method parameters must be a mapping: {method_name}")
    return FrontendConfig(
        method_name=method_name,
        method_version=str(method_cfg.get("method_version", "1.0")),
        parameters=dict(parameters),
    )


def _phase3_active_methods(args: argparse.Namespace, config: dict[str, Any]) -> list[str]:
    if args.method:
        return [args.method]
    signal_cfg = config.get("signal")
    if not isinstance(signal_cfg, dict):
        raise ValueError("Phase 3 config requires a signal section")
    comparison_cfg = signal_cfg.get("comparison", {})
    if not isinstance(comparison_cfg, dict):
        comparison_cfg = {}
    active_methods = comparison_cfg.get("active_methods")
    if not isinstance(active_methods, list) or not active_methods:
        raise ValueError("Phase 3 config requires signal.comparison.active_methods")
    return [str(item) for item in active_methods]


def _phase3_signal_sample(
    *,
    config: dict[str, Any],
    project_root: Path,
    registry: RegistryStore,
    dataset_name: str,
):
    signal_cfg = config.get("signal")
    if not isinstance(signal_cfg, dict):
        raise ValueError("Phase 3 config requires a signal section")
    series, _ = _load_geomagnetic_series_from_registry(project_root, registry, dataset_name)
    return build_signal_sample_from_timeseries(series, signal_cfg)


def _run_phase3_methods(
    *,
    config: dict[str, Any],
    project_root: Path,
    registry: RegistryStore,
    dataset_name: str,
    method_names: list[str],
    export_results: bool,
    build_report: bool,
) -> dict[str, Any]:
    signal_cfg = config["signal"]
    sample = _phase3_signal_sample(
        config=config,
        project_root=project_root,
        registry=registry,
        dataset_name=dataset_name,
    )
    sample_validation = validate_signal_sample(sample)
    results = []
    exports = []
    validations = [sample_validation]
    if sample_validation["ok"]:
        for method_name in method_names:
            frontend = build_frontend(method_name)
            frontend_config = _build_phase3_frontend_config(config, method_name)
            result = frontend.run(sample, frontend_config)
            result_validation = validate_frontend_result(result)
            validations.append(result_validation)
            results.append(result)
            if export_results:
                exports.append(
                    {
                        "method_name": method_name,
                        "paths": export_frontend_result(
                            project_root=project_root,
                            signal_config=signal_cfg,
                            signal_sample=sample,
                            result=result,
                        ),
                    }
                )

    comparison_report = None
    comparison_path = None
    if build_report and results:
        benchmark_type = str(sample.metadata.get("benchmark_type", "synthetic"))
        default_scope = "training" if benchmark_type == "synthetic" else "real_event_benchmark"
        promotion_status = "ready" if benchmark_type == "synthetic" else "provisional"
        promotion_reason = (
            "Synthetic benchmark winner becomes the current training default."
            if benchmark_type == "synthetic"
            else "Real benchmark remains informational until at least 3 stations, 3 event windows, and 2 policy agreements are available."
        )
        comparison_report = build_comparison_report(
            sample_id=sample.sample_id,
            results=results,
            comparison_config=signal_cfg.get("comparison", {}),
            benchmark_type=benchmark_type,
            default_scope=default_scope,
            promotion_status=promotion_status,
            promotion_reason=promotion_reason,
        )
        if signal_cfg.get("comparison", {}).get("export_report", True):
            comparison_path = export_comparison_report(
                project_root=project_root,
                signal_config=signal_cfg,
                comparison_report=comparison_report,
            )

    return {
        "sample": sample,
        "sample_validation": sample_validation,
        "results": results,
        "exports": exports,
        "validations": validations,
        "comparison_report": comparison_report,
        "comparison_path": comparison_path,
    }




def _phase3_benchmark_config(config: dict[str, Any]) -> tuple[str, list[str], dict[str, Any]]:
    signal_cfg = config.get("signal")
    if not isinstance(signal_cfg, dict):
        raise ValueError("Phase 3 config requires a signal section")
    benchmarks_cfg = signal_cfg.get("benchmarks", {})
    if not isinstance(benchmarks_cfg, dict):
        benchmarks_cfg = {}
    synthetic_dataset = str(benchmarks_cfg.get("synthetic_dataset") or signal_cfg.get("input_dataset"))
    real_event_datasets = benchmarks_cfg.get("real_event_datasets", [])
    if not isinstance(real_event_datasets, list):
        real_event_datasets = []
    promotion_policy = benchmarks_cfg.get("real_promotion_policy", {})
    if not isinstance(promotion_policy, dict):
        promotion_policy = {}
    return synthetic_dataset, [str(item) for item in real_event_datasets], dict(promotion_policy)


def _aggregate_real_benchmark(
    *,
    reports: list[dict[str, Any]],
    comparison_priority: list[str],
    promotion_policy: dict[str, Any],
) -> dict[str, Any]:
    method_scores: dict[str, list[float]] = {}
    window_scores: dict[str, dict[str, list[float]]] = {}
    time_ranges: set[str] = set()
    station_ids: set[str] = set()
    for item in reports:
        time_range = item.get("time_range")
        if isinstance(time_range, str) and time_range:
            time_ranges.add(time_range)
        station_id = item.get("station_id")
        if isinstance(station_id, str) and station_id:
            station_ids.add(station_id)
        report = item.get("report") or {}
        for row in report.get("summary_table", []):
            method_name = str(row["method_name"])
            score = float(row["score"])
            method_scores.setdefault(method_name, []).append(score)
            if isinstance(time_range, str) and time_range:
                window_scores.setdefault(time_range, {}).setdefault(method_name, []).append(score)

    def _priority_index(method_name: str) -> int:
        return comparison_priority.index(method_name) if method_name in comparison_priority else len(comparison_priority)

    rows = [
        {
            "method_name": method_name,
            "mean_score": sum(scores) / max(len(scores), 1),
            "report_count": len(scores),
        }
        for method_name, scores in method_scores.items()
    ]
    rows.sort(key=lambda item: (-float(item["mean_score"]), _priority_index(str(item["method_name"])), str(item["method_name"])))
    ranking = [str(item["method_name"]) for item in rows]

    window_win_counts = {str(item["method_name"]): 0 for item in rows}
    for method_scores_by_window in window_scores.values():
        window_rows = [
            {
                "method_name": method_name,
                "mean_score": sum(scores) / max(len(scores), 1),
            }
            for method_name, scores in method_scores_by_window.items()
        ]
        window_rows.sort(
            key=lambda item: (-float(item["mean_score"]), _priority_index(str(item["method_name"])), str(item["method_name"]))
        )
        if window_rows:
            winner = str(window_rows[0]["method_name"])
            window_win_counts[winner] = window_win_counts.get(winner, 0) + 1

    window_win_ranking = sorted(
        window_win_counts.items(),
        key=lambda item: (-int(item[1]), _priority_index(str(item[0])), str(item[0])),
    )
    mean_score_leader = ranking[0] if ranking else ""
    window_wins_leader = window_win_ranking[0][0] if window_win_ranking else ""
    policy_agreement_count = 2 if mean_score_leader and mean_score_leader == window_wins_leader else 0

    min_stations = int(promotion_policy.get("min_stations", 3))
    min_events = int(promotion_policy.get("min_event_windows", 3))
    required_consensus = int(promotion_policy.get("required_policy_consensus", 2))
    station_count = len(station_ids)
    event_count = len(time_ranges)
    dataset_count = len(reports)
    ready = (
        station_count >= min_stations
        and event_count >= min_events
        and policy_agreement_count >= required_consensus
    )
    promotion_status = "ready" if ready else "provisional"
    policy_leaders = {
        "mean_score": mean_score_leader,
        "window_wins": window_wins_leader,
    }
    promotion_reason = (
        "Real-event benchmark satisfies current promotion thresholds. "
        f"mean_score leader={mean_score_leader}, window_wins leader={window_wins_leader}."
        if ready
        else (
            "Current real benchmark coverage is "
            f"{station_count} station(s), {event_count} event window(s), {dataset_count} dataset(s), "
            f"and {policy_agreement_count} policy agreement(s); thresholds are {min_stations} stations, "
            f"{min_events} events, and {required_consensus} policy agreements. "
            f"mean_score leader={mean_score_leader}, window_wins leader={window_wins_leader}."
        )
    )
    return {
        "benchmark_type": "real_event",
        "ranking": ranking,
        "default_method": ranking[0] if ranking else "",
        "summary_table": rows,
        "observed_station_count": station_count,
        "observed_event_window_count": event_count,
        "observed_dataset_count": dataset_count,
        "policy_leaders": policy_leaders,
        "policy_agreement_count": policy_agreement_count,
        "window_win_counts": window_win_counts,
        "promotion_status": promotion_status,
        "promotion_reason": promotion_reason,
    }
def _build_phase4_graph_assets(
    *,
    config: dict[str, Any],
    project_root: Path,
) -> dict[str, Any]:
    graph_cfg = config.get("graph")
    if not isinstance(graph_cfg, dict):
        raise ValueError("Phase 4 config requires a graph section")

    task, build_context, graph_samples = build_graph_samples_from_config(project_root, config)
    scenario_ids = sorted({str(item.scenario_id) for item in graph_samples if str(item.scenario_id)})
    scenario_group_assignments = (
        {item.graph_id: str(item.scenario_id) for item in graph_samples}
        if len(scenario_ids) > 1
        else None
    )
    split_assignments = build_split_assignments(
        [item.graph_id for item in graph_samples],
        graph_cfg.get("split", {}),
        group_assignments=scenario_group_assignments,
    )
    validations = [validate_graph_sample(item) for item in graph_samples]
    validation_summary = summarize_validation_results(validations)
    first_sample = graph_samples[0] if graph_samples else None
    graph_report = {
        "dataset_name": build_context["dataset_name"],
        "source_case_id": build_context["source_case_id"],
        "scenario_id": build_context["scenario_id"],
        "scenario_ids": build_context.get("scenario_ids", []),
        "graph_count": len(graph_samples),
        "node_count": len(first_sample.node_records) if first_sample else 0,
        "edge_count": len(first_sample.edge_records) if first_sample else 0,
        "feature_count": len(first_sample.feature_bundle.node_feature_names) if first_sample else 0,
        "feature_names": first_sample.feature_bundle.node_feature_names if first_sample else [],
        "target_level": task.target_level,
        "objective": task.objective,
        "node_type": task.node_type,
        "sparsity_rate": task.sparsity_rate,
        "include_signal_features": task.include_signal_features,
        "include_physics_baseline": task.include_physics_baseline,
        "sample_ids": [item.sample_id for item in graph_samples],
        "graph_ids": [item.graph_id for item in graph_samples],
        "split_assignments": split_assignments,
        "validation_summary": validation_summary,
        "scenario_grouped_split": True,
    }
    return {
        "task": task,
        "build_context": build_context,
        "graph_samples": graph_samples,
        "split_assignments": split_assignments,
        "validations": validations,
        "validation_summary": validation_summary,
        "graph_report": graph_report,
    }


def cmd_graph_build_samples(args: argparse.Namespace) -> int:
    config, project_root = _load_phase4_context(args)
    context, _ = initialize_run(
        config=config,
        config_path=str(Path(args.config).resolve()),
        command="graph-build-samples",
        project_root=project_root,
    )
    logger = configure_logger("gic.phase4.graph_build", config["logging"]["level"], context.log_file)
    payload = _build_phase4_graph_assets(config=config, project_root=project_root)
    validation_summary = payload["validation_summary"]
    graph_report = payload["graph_report"]
    validation_report_path = write_validation_report(validation_summary, context.report_dir / "graph_build_validation_report.json")
    graph_report_path = context.report_dir / "graph_build_report.json"
    graph_report_path.write_text(json.dumps(graph_report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_summary(
        context,
        {
            "status": "ok" if validation_summary["error_count"] == 0 else "failed",
            "dataset_name": graph_report["dataset_name"],
            "graph_count": graph_report["graph_count"],
            "validation_report_path": str(validation_report_path),
            "graph_report_path": str(graph_report_path),
        },
    )
    logger.info("Built %d graph samples for dataset %s", graph_report["graph_count"], graph_report["dataset_name"])
    _serialize_result(
        {
            "run_id": context.run_id,
            "dataset_name": graph_report["dataset_name"],
            "graph_count": graph_report["graph_count"],
            "node_count": graph_report["node_count"],
            "edge_count": graph_report["edge_count"],
            "feature_count": graph_report["feature_count"],
            "split_assignments": graph_report["split_assignments"],
            "validation_summary": validation_summary,
            "validation_report_path": str(validation_report_path),
            "graph_report_path": str(graph_report_path),
        }
    )
    return 0 if validation_summary["error_count"] == 0 else 1


def cmd_graph_export_dataset(args: argparse.Namespace) -> int:
    config, project_root = _load_phase4_context(args)
    context, _ = initialize_run(
        config=config,
        config_path=str(Path(args.config).resolve()),
        command="graph-export-dataset",
        project_root=project_root,
    )
    logger = configure_logger("gic.phase4.graph_export", config["logging"]["level"], context.log_file)
    try:
        export_payload = _phase4_export_dataset(config=config, project_root=project_root)
    except ValueError as exc:
        payload = _build_phase4_graph_assets(config=config, project_root=project_root)
        validation_summary = payload["validation_summary"]
        validation_report_path = write_validation_report(validation_summary, context.report_dir / "graph_build_validation_report.json")
        write_summary(
            context,
            {
                "status": "failed",
                "dataset_name": payload["graph_report"]["dataset_name"],
                "validation_report_path": str(validation_report_path),
                "error": str(exc),
            },
        )
        _serialize_result(
            {
                "run_id": context.run_id,
                "dataset_name": payload["graph_report"]["dataset_name"],
                "validation_summary": validation_summary,
                "validation_report_path": str(validation_report_path),
                "error": str(exc),
            }
        )
        return 1

    payload = export_payload["payload"]
    export_report = export_payload["export_report"]
    combined_summary = export_payload["combined_summary"]
    export_report_path = context.report_dir / "graph_export_report.json"
    export_report_path.write_text(json.dumps(export_report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_summary(
        context,
        {
            "status": "ok" if combined_summary["error_count"] == 0 else "failed",
            "dataset_name": payload["graph_report"]["dataset_name"],
            "manifest_path": export_payload["manifest"].paths["manifest"],
            "dataset_path": export_payload["dataset_path"],
            "graph_count": len(export_payload["graph_paths"]),
        },
    )
    logger.info("Exported graph-ready dataset %s with %d samples", payload["graph_report"]["dataset_name"], len(export_payload["graph_paths"]))
    _serialize_result(
        {
            "run_id": context.run_id,
            "dataset_name": payload["graph_report"]["dataset_name"],
            "manifest_path": export_payload["manifest"].paths["manifest"],
            "dataset_path": export_payload["dataset_path"],
            "graph_count": len(export_payload["graph_paths"]),
            "split_assignments": payload["split_assignments"],
            "validation_summary": combined_summary,
            "export_report_path": str(export_report_path),
        }
    )
    return 0 if combined_summary["error_count"] == 0 else 1


def cmd_graph_build_report(args: argparse.Namespace) -> int:
    config, project_root = _load_phase4_context(args)
    context, _ = initialize_run(
        config=config,
        config_path=str(Path(args.config).resolve()),
        command="graph-build-report",
        project_root=project_root,
    )
    logger = configure_logger("gic.phase4.graph_report", config["logging"]["level"], context.log_file)
    export_payload = _phase4_export_dataset(config=config, project_root=project_root)
    report_cfg = _phase4_report_config(config)
    report_training_config = _phase4_training_override(config, report_cfg["training_epochs"])
    active_models = _phase4_active_models(config)
    default_runs: list[dict[str, Any]] = []
    model_reports_root = ensure_directory(context.artifact_dir / "baseline_models")
    for model_type in active_models:
        run_payload = _phase4_train_and_evaluate(
            config=report_training_config,
            model_type=model_type,
            dataset_path=export_payload["dataset_path"],
            output_root=model_reports_root,
            split=report_cfg["compare_split"],
        )
        evaluation = run_payload["evaluation"]
        predictions_path = write_json_report(
            evaluation["rows"],
            context.report_dir / f"{model_type}_{report_cfg['compare_split']}_predictions.json",
        )
        metrics_path = write_json_report(
            evaluation["metrics"],
            context.report_dir / f"{model_type}_{report_cfg['compare_split']}_metrics.json",
        )
        reconstruction_path = write_json_report(
            evaluation["reconstruction_maps"],
            context.report_dir / f"{model_type}_{report_cfg['compare_split']}_reconstruction_maps.json",
        )
        default_runs.append(
            {
                "model_type": model_type,
                "dataset_path": evaluation["dataset_path"],
                "checkpoint_path": run_payload["checkpoint_path"],
                "history_path": run_payload["history_path"],
                "predictions_path": str(predictions_path),
                "metrics_path": str(metrics_path),
                "reconstruction_path": str(reconstruction_path),
                "metrics": evaluation["metrics"],
            }
        )

    comparison = _phase4_comparison_summary(default_runs)
    graph_cfg = config["graph"]
    default_dataset_name = str(graph_cfg["dataset_name"])
    ablation_rows_sparsity: list[dict[str, Any]] = []
    ablation_rows_features: list[dict[str, Any]] = []
    for sparsity_rate in report_cfg["sparsity_rates"]:
        variant_name = _phase4_variant_name(default_dataset_name, f"s{int(round(sparsity_rate * 100)):02d}")
        variant_config = _phase4_variant_config(
            config,
            dataset_name=variant_name,
            sparsity_rate=sparsity_rate,
        )
        variant_export = _phase4_export_dataset(config=variant_config, project_root=project_root)
        variant_training = _phase4_training_override(variant_config, report_cfg["training_epochs"])
        for model_type in report_cfg["ablation_models"]:
            run_payload = _phase4_train_and_evaluate(
                config=variant_training,
                model_type=model_type,
                dataset_path=variant_export["dataset_path"],
                output_root=ensure_directory(context.artifact_dir / "ablations" / "sparsity" / variant_name),
                split=report_cfg["compare_split"],
            )
            ablation_rows_sparsity.append(
                _phase4_variant_summary(
                    {
                        "variant_name": variant_name,
                        "model_type": model_type,
                        "dataset_path": variant_export["dataset_path"],
                        "sparsity_rate": sparsity_rate,
                        "include_signal_features": bool(variant_config["graph"].get("include_signal_features", False)),
                        "include_physics_baseline": bool(variant_config["graph"].get("include_physics_baseline", False)),
                        "metrics": run_payload["evaluation"]["metrics"],
                    },
                    report_cfg["compare_split"],
                )
            )

    if report_cfg["run_feature_ablations"]:
        feature_variants = [
            ("signal_off", {"include_signal_features": False}),
            ("physics_off", {"include_physics_baseline": False}),
        ]
        for suffix, overrides in feature_variants:
            variant_name = _phase4_variant_name(default_dataset_name, suffix)
            variant_config = _phase4_variant_config(
                config,
                dataset_name=variant_name,
                include_signal_features=overrides.get("include_signal_features"),
                include_physics_baseline=overrides.get("include_physics_baseline"),
            )
            variant_export = _phase4_export_dataset(config=variant_config, project_root=project_root)
            variant_training = _phase4_training_override(variant_config, report_cfg["training_epochs"])
            for model_type in report_cfg["ablation_models"]:
                run_payload = _phase4_train_and_evaluate(
                    config=variant_training,
                    model_type=model_type,
                    dataset_path=variant_export["dataset_path"],
                    output_root=ensure_directory(context.artifact_dir / "ablations" / "features" / variant_name),
                    split=report_cfg["compare_split"],
                )
                ablation_rows_features.append(
                    _phase4_variant_summary(
                        {
                            "variant_name": variant_name,
                            "model_type": model_type,
                            "dataset_path": variant_export["dataset_path"],
                            "sparsity_rate": float(variant_config["graph"].get("sparsity_rate", 0.0)),
                            "include_signal_features": bool(variant_config["graph"].get("include_signal_features", False)),
                            "include_physics_baseline": bool(variant_config["graph"].get("include_physics_baseline", False)),
                            "metrics": run_payload["evaluation"]["metrics"],
                        },
                        report_cfg["compare_split"],
                    )
                )

    report_payload = {
        "dataset_name": export_payload["payload"]["graph_report"]["dataset_name"],
        "compare_split": report_cfg["compare_split"],
        "active_models": active_models,
        "default_dataset": {
            "dataset_name": export_payload["payload"]["graph_report"]["dataset_name"],
            "dataset_path": export_payload["dataset_path"],
            "manifest_path": export_payload["manifest"].paths["manifest"],
            "graph_report": export_payload["payload"]["graph_report"],
            "validation_summary": export_payload["combined_summary"],
        },
        "comparison": comparison,
        "ablations": {
            "sparsity": ablation_rows_sparsity,
            "features": ablation_rows_features,
        },
    }
    report_path = write_json_report(report_payload, context.report_dir / "phase4_baseline_report.json")
    markdown_path = write_markdown_report(_phase4_markdown_report(report_payload), context.report_dir / "phase4_baseline_report.md")
    write_summary(
        context,
        {
            "status": "ok",
            "dataset_name": export_payload["payload"]["graph_report"]["dataset_name"],
            "graph_count": export_payload["payload"]["graph_report"]["graph_count"],
            "report_path": str(report_path),
            "markdown_path": str(markdown_path),
            "default_graph_baseline": comparison["default_graph_baseline"],
        },
    )
    logger.info("Built Phase 4 baseline report for dataset %s", export_payload["payload"]["graph_report"]["dataset_name"])
    _serialize_result(
        {
            "run_id": context.run_id,
            "dataset_name": export_payload["payload"]["graph_report"]["dataset_name"],
            "report_path": str(report_path),
            "markdown_path": str(markdown_path),
            "comparison": comparison,
            "ablation_counts": {
                "sparsity": len(ablation_rows_sparsity),
                "features": len(ablation_rows_features),
            },
        }
    )
    return 0


def _phase4_dataset_path(config: dict[str, Any], project_root: Path, override: str | None = None) -> Path:
    if isinstance(override, str) and override:
        return Path(override).resolve()
    graph_cfg = config.get("graph")
    if not isinstance(graph_cfg, dict):
        raise ValueError("Phase 4 config requires a graph section")
    output_root = graph_cfg.get("output_root")
    dataset_name = graph_cfg.get("dataset_name")
    if not isinstance(output_root, str) or not output_root:
        raise ValueError("Phase 4 config requires graph.output_root")
    if not isinstance(dataset_name, str) or not dataset_name:
        raise ValueError("Phase 4 config requires graph.dataset_name")
    return (project_root / output_root / "datasets" / f"{dataset_name}.json").resolve()


def _phase4_model_type(model_type: str | None) -> str:
    return str(model_type or "mlp").strip().lower()


def _phase4_training_override(config: dict[str, Any], epochs: int | None) -> dict[str, Any]:
    if epochs is None:
        return config
    updated = json.loads(json.dumps(config))
    training_cfg = dict(updated.get("training", {}))
    training_cfg["epochs"] = int(epochs)
    updated["training"] = training_cfg
    return updated


def _phase4_clone_config(config: dict[str, Any]) -> dict[str, Any]:
    return json.loads(json.dumps(config))


def _phase4_active_models(config: dict[str, Any]) -> list[str]:
    baseline_cfg = config.get("baseline", {})
    if not isinstance(baseline_cfg, dict):
        baseline_cfg = {}
    active_models = baseline_cfg.get("active_models", ["mlp", "gcn", "graphsage", "gat"])
    if not isinstance(active_models, list) or not active_models:
        raise ValueError("Phase 4 config requires baseline.active_models")
    return [_phase4_model_type(str(item)) for item in active_models]


def _phase4_report_config(config: dict[str, Any]) -> dict[str, Any]:
    reporting_cfg = config.get("reporting", {})
    if not isinstance(reporting_cfg, dict):
        reporting_cfg = {}
    return {
        "training_epochs": int(reporting_cfg.get("training_epochs", 4)),
        "compare_split": str(reporting_cfg.get("compare_split", "test")),
        "ablation_models": [_phase4_model_type(str(item)) for item in reporting_cfg.get("ablation_models", ["mlp", "gcn"])],
        "sparsity_rates": [float(item) for item in reporting_cfg.get("sparsity_rates", [0.3, 0.7, 0.9])],
        "run_feature_ablations": bool(reporting_cfg.get("run_feature_ablations", True)),
    }


def _phase4_variant_config(
    config: dict[str, Any],
    *,
    dataset_name: str,
    sparsity_rate: float | None = None,
    include_signal_features: bool | None = None,
    include_physics_baseline: bool | None = None,
) -> dict[str, Any]:
    updated = _phase4_clone_config(config)
    graph_cfg = dict(updated.get("graph", {}))
    graph_cfg["dataset_name"] = dataset_name
    if sparsity_rate is not None:
        graph_cfg["sparsity_rate"] = float(sparsity_rate)
    if include_signal_features is not None:
        graph_cfg["include_signal_features"] = bool(include_signal_features)
    if include_physics_baseline is not None:
        graph_cfg["include_physics_baseline"] = bool(include_physics_baseline)
    updated["graph"] = graph_cfg
    return updated


def _phase4_export_dataset(config: dict[str, Any], project_root: Path) -> dict[str, Any]:
    payload = _build_phase4_graph_assets(config=config, project_root=project_root)
    validation_summary = payload["validation_summary"]
    if validation_summary["error_count"] > 0:
        raise ValueError(f"Phase 4 graph validation failed for {payload['graph_report']['dataset_name']}: {validation_summary}")
    graph_cfg = config["graph"]
    manifest, graph_paths = export_graph_samples(
        project_root=project_root,
        graph_config=graph_cfg,
        dataset_name=payload["build_context"]["dataset_name"],
        source_case_id=payload["build_context"]["source_case_id"],
        scenario_id=payload["build_context"]["scenario_id"],
        task_payload=payload["build_context"]["task"],
        graph_samples=payload["graph_samples"],
        split_assignments=payload["split_assignments"],
    )
    dataset_path = export_graph_dataset(project_root=project_root, graph_config=graph_cfg, manifest=manifest)
    reloaded_manifest = load_graph_manifest(manifest.paths["manifest"])
    manifest_validation = validate_graph_manifest(reloaded_manifest)
    combined_summary = summarize_validation_results([*payload["validations"], manifest_validation])
    export_report = dict(payload["graph_report"])
    export_report.update(
        {
            "manifest_path": manifest.paths["manifest"],
            "dataset_path": dataset_path,
            "graph_paths": graph_paths,
            "manifest_validation": manifest_validation,
            "validation_summary": combined_summary,
        }
    )
    return {
        "payload": payload,
        "manifest": manifest,
        "graph_paths": graph_paths,
        "dataset_path": dataset_path,
        "manifest_validation": manifest_validation,
        "combined_summary": combined_summary,
        "export_report": export_report,
    }


def _phase4_train_and_evaluate(
    *,
    config: dict[str, Any],
    model_type: str,
    dataset_path: str | Path,
    output_root: Path,
    split: str,
) -> dict[str, Any]:
    model_output_root = ensure_directory(output_root / model_type)
    train_result = train_baseline_model(
        model_type=model_type,
        config=config,
        dataset_path=dataset_path,
        output_dir=model_output_root,
    )
    eval_payload = evaluate_baseline_model(
        model_type=model_type,
        config=config,
        dataset_path=dataset_path,
        checkpoint_path=train_result.checkpoint_path,
        split=split,
    )
    return {
        "model_type": model_type,
        "checkpoint_path": train_result.checkpoint_path,
        "history_path": train_result.history_path,
        "training_result": train_result,
        "evaluation": eval_payload,
        "metrics": eval_payload["metrics"],
    }


def _phase4_hidden_mae(row: dict[str, Any]) -> float:
    return float(row.get("metrics", {}).get("hidden_only", {}).get("mae", row.get("metrics", {}).get("overall", {}).get("mae", float("inf"))))


def _phase4_comparison_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    ranked_rows = compare_metric_rows(rows)
    default_graph_row = next((item for item in ranked_rows if str(item.get("model_type")) != "mlp"), None)
    mlp_row = next((item for item in rows if str(item.get("model_type")) == "mlp"), None)
    graph_gain = None
    graph_beats_non_graph = None
    if default_graph_row is not None and mlp_row is not None:
        graph_gain = _phase4_hidden_mae(mlp_row) - _phase4_hidden_mae(default_graph_row)
        graph_beats_non_graph = _phase4_hidden_mae(default_graph_row) < _phase4_hidden_mae(mlp_row)
    return {
        "ranking": [str(item.get("model_type", "")) for item in ranked_rows],
        "rows": ranked_rows,
        "best_overall_model": str(ranked_rows[0].get("model_type", "")) if ranked_rows else "",
        "default_graph_baseline": str(default_graph_row.get("model_type", "")) if default_graph_row else "",
        "graph_vs_non_graph_hidden_mae_gain": graph_gain,
        "graph_beats_non_graph_on_hidden_mae": graph_beats_non_graph,
    }


def _phase4_variant_name(base_name: str, suffix: str) -> str:
    return f"{base_name}_{suffix}"


def _phase4_variant_summary(row: dict[str, Any], split: str) -> dict[str, Any]:
    metrics = row["metrics"]
    return {
        "variant_name": str(row["variant_name"]),
        "model_type": str(row["model_type"]),
        "split": split,
        "dataset_path": str(row["dataset_path"]),
        "sparsity_rate": float(row["sparsity_rate"]),
        "include_signal_features": bool(row["include_signal_features"]),
        "include_physics_baseline": bool(row["include_physics_baseline"]),
        "metrics": metrics,
        "hidden_mae": float(metrics.get("hidden_only", {}).get("mae", metrics.get("overall", {}).get("mae", 0.0))),
    }


def _phase4_markdown_report(report: dict[str, Any]) -> str:
    comparison = report["comparison"]
    lines = [
        "# Phase 4 Baseline Report",
        "",
        "## Default Dataset",
        f"- Dataset: `{report['default_dataset']['dataset_name']}`",
        f"- Split: `{report['compare_split']}`",
        f"- Active models: {', '.join(report['active_models'])}",
        f"- Best overall model: `{comparison['best_overall_model']}`",
        f"- Default graph baseline: `{comparison['default_graph_baseline']}`",
        f"- Graph beats non-graph on hidden MAE: `{comparison['graph_beats_non_graph_on_hidden_mae']}`",
    ]
    gain = comparison.get("graph_vs_non_graph_hidden_mae_gain")
    if gain is not None:
        lines.append(f"- Hidden MAE gain vs `mlp`: `{gain:.6f}`")
    lines.extend(["", "## Baseline Ranking"])
    for row in comparison["rows"]:
        hidden_mae = _phase4_hidden_mae(row)
        overall_mae = float(row.get("metrics", {}).get("overall", {}).get("mae", 0.0))
        lines.append(
            f"- `{row['model_type']}`: hidden_mae={hidden_mae:.6f}, overall_mae={overall_mae:.6f}, checkpoint=`{row['checkpoint_path']}`"
        )
    lines.extend(["", "## Sparsity Ablation"])
    for row in report["ablations"]["sparsity"]:
        lines.append(
            f"- `{row['variant_name']}` / `{row['model_type']}`: sparsity={row['sparsity_rate']:.1f}, hidden_mae={row['hidden_mae']:.6f}"
        )
    lines.extend(["", "## Feature Ablation"])
    for row in report["ablations"]["features"]:
        lines.append(
            f"- `{row['variant_name']}` / `{row['model_type']}`: signal={row['include_signal_features']}, physics={row['include_physics_baseline']}, hidden_mae={row['hidden_mae']:.6f}"
        )
    lines.extend(["", "## Acceptance Note"])
    if comparison["graph_beats_non_graph_on_hidden_mae"]:
        lines.append("- Current graph baseline outperforms the Phase 4 non-graph baseline on hidden-node MAE for the default dataset.")
    else:
        lines.append("- Current graph baseline does not yet show a clear hidden-node MAE gain over the non-graph baseline on the default dataset.")
    lines.append("- Phase 4 implementation scope is complete when read as code/assets/tests/reporting coverage; empirical promotion to later phases should still follow the documented acceptance check.")
    return "\n".join(lines) + "\n"


def cmd_train_baseline(args: argparse.Namespace) -> int:
    config, project_root = _load_phase4_context(args)
    config = _phase4_training_override(config, args.epochs)
    model_type = _phase4_model_type(args.model_type)
    dataset_path = _phase4_dataset_path(config, project_root, args.dataset_path)
    if not dataset_path.exists():
        raise FileNotFoundError(f"graph-ready data missing: {dataset_path}")
    context, _ = initialize_run(
        config=config,
        config_path=str(Path(args.config).resolve()),
        command="train-baseline",
        project_root=project_root,
    )
    logger = configure_logger("gic.phase4.train", config["logging"]["level"], context.log_file)
    result = train_baseline_model(model_type=model_type, config=config, dataset_path=dataset_path, output_dir=context.artifact_dir)
    metrics_report_path = write_json_report(
        {
            "validation_metrics": result.validation_metrics,
            "test_metrics": result.test_metrics,
            "best_epoch": result.best_epoch,
            "input_dim": result.input_dim,
            "train_example_count": result.train_example_count,
            "val_example_count": result.val_example_count,
            "test_example_count": result.test_example_count,
        },
        context.report_dir / f"{model_type}_training_metrics.json",
    )
    write_summary(
        context,
        {
            "status": "ok",
            "model_type": result.model_type,
            "checkpoint_path": result.checkpoint_path,
            "history_path": result.history_path,
            "metrics_report_path": str(metrics_report_path),
        },
    )
    logger.info("Trained %s baseline on %s", result.model_type, dataset_path)
    _serialize_result(
        {
            "run_id": context.run_id,
            "model_type": result.model_type,
            "dataset_path": str(dataset_path),
            "checkpoint_path": result.checkpoint_path,
            "history_path": result.history_path,
            "metrics_report_path": str(metrics_report_path),
            "best_epoch": result.best_epoch,
            "validation_metrics": result.validation_metrics,
            "test_metrics": result.test_metrics,
        }
    )
    return 0


def cmd_eval_baseline(args: argparse.Namespace) -> int:
    config, project_root = _load_phase4_context(args)
    model_type = _phase4_model_type(args.model_type)
    dataset_path = _phase4_dataset_path(config, project_root, args.dataset_path)
    if not dataset_path.exists():
        raise FileNotFoundError(f"graph-ready data missing: {dataset_path}")
    if not args.checkpoint:
        raise ValueError("eval-baseline requires --checkpoint")
    checkpoint_path = Path(args.checkpoint).resolve()
    if not checkpoint_path.exists():
        raise FileNotFoundError(f"checkpoint missing: {checkpoint_path}")
    context, _ = initialize_run(
        config=config,
        config_path=str(Path(args.config).resolve()),
        command="eval-baseline",
        project_root=project_root,
    )
    logger = configure_logger("gic.phase4.eval", config["logging"]["level"], context.log_file)
    payload = evaluate_baseline_model(
        model_type=model_type,
        config=config,
        dataset_path=dataset_path,
        checkpoint_path=checkpoint_path,
        split=str(args.split or "test"),
    )
    predictions_path = write_json_report(payload["rows"], context.report_dir / f"{model_type}_{payload['split']}_predictions.json")
    metrics_path = write_json_report(payload["metrics"], context.report_dir / f"{model_type}_{payload['split']}_metrics.json")
    reconstruction_path = write_json_report(payload["reconstruction_maps"], context.report_dir / f"{model_type}_{payload['split']}_reconstruction_maps.json")
    write_summary(
        context,
        {
            "status": "ok",
            "model_type": model_type,
            "split": payload["split"],
            "checkpoint_path": str(checkpoint_path),
            "predictions_path": str(predictions_path),
            "metrics_path": str(metrics_path),
            "reconstruction_path": str(reconstruction_path),
        },
    )
    logger.info("Evaluated %s baseline on split %s", model_type, payload["split"])
    _serialize_result(
        {
            "run_id": context.run_id,
            "model_type": model_type,
            "split": payload["split"],
            "dataset_path": payload["dataset_path"],
            "checkpoint_path": str(checkpoint_path),
            "predictions_path": str(predictions_path),
            "metrics_path": str(metrics_path),
            "reconstruction_path": str(reconstruction_path),
            "metrics": payload["metrics"],
        }
    )
    return 0


def cmd_show_config(args: argparse.Namespace) -> int:
    config = load_config(args.config)
    print(dump_config(config))
    return 0


def cmd_init_run(args: argparse.Namespace) -> int:
    config = load_config(args.config)
    context, metadata = initialize_run(
        config=config,
        config_path=str(Path(args.config).resolve()),
        command="init-run",
        project_root=args.project_root,
    )
    _serialize_result(
        {
            "config_path": metadata["config_path"],
            "log_file": str(context.log_file),
            "metadata_path": str(context.metadata_path),
            "run_id": context.run_id,
            "summary_path": str(context.summary_path),
        }
    )
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    config = load_config(args.config)
    context, metadata = initialize_run(
        config=config,
        config_path=str(Path(args.config).resolve()),
        command="run",
        project_root=args.project_root,
    )
    logger = configure_logger("gic.phase0", config["logging"]["level"], context.log_file)
    logger.info("Starting Phase 0 dry run")
    logger.info("Loaded config from %s", metadata["config_path"])
    logger.info("Run ID: %s", context.run_id)

    summary = {
        "status": "ok",
        "stage": config["project"]["stage"],
        "profile": config["project"].get("profile", "default"),
        "mode": config["runtime"]["mode"],
        "run_id": context.run_id,
    }
    write_summary(context, summary)
    logger.info("Wrote summary to %s", context.summary_path)
    logger.info("Phase 0 dry run completed")

    _serialize_result(
        {
            "artifact_dir": str(context.artifact_dir),
            "log_file": str(context.log_file),
            "run_id": context.run_id,
            "summary_path": str(context.summary_path),
        }
    )
    return 0


def cmd_validate_env(_: argparse.Namespace) -> int:
    payload: dict[str, Any] = {
        "conda_env": os.environ.get("CONDA_DEFAULT_ENV", ""),
        "cwd": str(Path.cwd().resolve()),
        "python_executable": sys.executable,
        "python_version": platform.python_version(),
        "wsl_distro": os.environ.get("WSL_DISTRO_NAME", ""),
    }
    try:
        import torch  # type: ignore

        payload["torch"] = {
            "version": torch.__version__,
            "cuda_available": torch.cuda.is_available(),
            "cuda_device_count": torch.cuda.device_count(),
        }
        if torch.cuda.is_available() and torch.cuda.device_count() > 0:
            payload["torch"]["cuda_device_0"] = torch.cuda.get_device_name(0)
    except Exception as exc:  # pragma: no cover
        payload["torch"] = {"error": f"{type(exc).__name__}: {exc}"}
    _serialize_result(payload)
    return 0


def cmd_data_list_sources(args: argparse.Namespace) -> int:
    _, _, registry = _load_phase1_context(args)
    _serialize_result({"sources": [to_dict(item) for item in registry.list_sources()]})
    return 0


def cmd_data_list_datasets(args: argparse.Namespace) -> int:
    _, _, registry = _load_phase1_context(args)
    _serialize_result({"datasets": [to_dict(item) for item in registry.list_datasets()]})
    return 0


def cmd_data_validate(args: argparse.Namespace) -> int:
    config, project_root, registry = _load_phase1_context(args)
    context, _ = initialize_run(
        config=config,
        config_path=str(Path(args.config).resolve()),
        command="data-validate",
        project_root=project_root,
    )
    logger = configure_logger("gic.phase1.validate", config["logging"]["level"], context.log_file)
    logger.info("Starting Phase 1 data validation")
    results = _validate_active_assets(project_root, registry)
    summary = summarize_validation_results(results)
    report_path = write_validation_report(summary, context.report_dir / "data_validation_report.json")
    write_summary(
        context,
        {
            "status": "ok" if summary["error_count"] == 0 else "failed",
            "run_id": context.run_id,
            "report_path": str(report_path),
            "result_count": summary["result_count"],
            "error_count": summary["error_count"],
            "warning_count": summary["warning_count"],
        },
    )
    logger.info("Validation report written to %s", report_path)
    _serialize_result(
        {
            "run_id": context.run_id,
            "report_path": str(report_path),
            "summary": summary,
        }
    )
    return 0 if summary["error_count"] == 0 else 1


def cmd_data_build_manifest(args: argparse.Namespace) -> int:
    config, project_root, registry = _load_phase1_context(args)
    dataset_name = args.dataset_name
    if not dataset_name:
        raise ValueError("data-build-manifest requires --dataset-name")
    context, _ = initialize_run(
        config=config,
        config_path=str(Path(args.config).resolve()),
        command="data-build-manifest",
        project_root=project_root,
    )
    logger = configure_logger("gic.phase1.manifest", config["logging"]["level"], context.log_file)
    payload, manifest = _convert_dataset(
        project_root=project_root,
        config=config,
        registry=registry,
        dataset_name=dataset_name,
    )
    write_summary(context, {"status": "ok", "dataset_name": dataset_name, "manifest": manifest})
    logger.info("Built manifest for dataset %s", dataset_name)
    _serialize_result(payload)
    return 0


def cmd_data_convert_sample(args: argparse.Namespace) -> int:
    config, project_root, registry = _load_phase1_context(args)
    dataset_names = [args.dataset_name] if args.dataset_name else [item.dataset_name for item in registry.active_datasets()]
    context, _ = initialize_run(
        config=config,
        config_path=str(Path(args.config).resolve()),
        command="data-convert-sample",
        project_root=project_root,
    )
    logger = configure_logger("gic.phase1.convert", config["logging"]["level"], context.log_file)
    outputs = []
    manifests = []
    for dataset_name in dataset_names:
        payload, manifest = _convert_dataset(
            project_root=project_root,
            config=config,
            registry=registry,
            dataset_name=dataset_name,
        )
        outputs.append(payload)
        manifests.append(manifest)
        logger.info("Converted dataset %s -> %s", dataset_name, payload["output_path"])
    write_summary(context, {"status": "ok", "datasets": dataset_names, "outputs": outputs})
    _serialize_result({"run_id": context.run_id, "outputs": outputs, "manifest_count": len(manifests)})
    return 0


def cmd_physics_build_case(args: argparse.Namespace) -> int:
    config, project_root, registry = _load_phase2_context(args)
    scenario_cfg = config["scenario"]
    grid_case, _ = _load_grid_case_from_registry(project_root, registry, scenario_cfg["case_dataset"])
    physics_case = convert_grid_case_to_physics(grid_case, config["physics"])
    outputs_root = ensure_directory(project_root / config["physics"]["outputs"]["physics_ready_root"])
    destination = outputs_root / f"{physics_case.case_id}.json"
    destination.write_text(json.dumps(to_dict(physics_case), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    _serialize_result({"case_id": physics_case.case_id, "output_path": str(destination)})
    return 0


def cmd_physics_solve_snapshot(args: argparse.Namespace) -> int:
    config, project_root, registry = _load_phase2_context(args)
    context, _ = initialize_run(
        config=config,
        config_path=str(Path(args.config).resolve()),
        command="physics-solve-snapshot",
        project_root=project_root,
    )
    logger = configure_logger("gic.phase2.snapshot", config["logging"]["level"], context.log_file)
    outputs, reports = _solve_physics_mode(
        config=config,
        project_root=project_root,
        registry=registry,
        scenario_mode="uniform_field",
    )
    write_summary(context, {"status": "ok", "outputs": outputs, "reports": reports})
    logger.info("Completed uniform snapshot physics solve")
    _serialize_result({"run_id": context.run_id, "outputs": outputs, "reports": reports})
    return 0


def cmd_physics_solve_series(args: argparse.Namespace) -> int:
    config, project_root, registry = _load_phase2_context(args)
    context, _ = initialize_run(
        config=config,
        config_path=str(Path(args.config).resolve()),
        command="physics-solve-series",
        project_root=project_root,
    )
    logger = configure_logger("gic.phase2.series", config["logging"]["level"], context.log_file)
    outputs, reports = _solve_physics_mode(
        config=config,
        project_root=project_root,
        registry=registry,
        scenario_mode="timeseries_field",
    )
    write_summary(context, {"status": "ok", "outputs": outputs, "reports": reports})
    logger.info("Completed time-series physics solve")
    _serialize_result({"run_id": context.run_id, "outputs": outputs, "reports": reports})
    return 0


def cmd_physics_generate_scenarios(args: argparse.Namespace) -> int:
    config, project_root, _ = _load_phase2_context(args)
    scenario_mode = args.scenario_mode or config["scenario"].get("type", "uniform_field")
    scenarios = generate_scenarios(config, scenario_mode)
    datasets_root = ensure_directory(project_root / config["physics"]["outputs"]["datasets_root"])
    destination = datasets_root / f"generated_{scenario_mode}_scenarios.json"
    destination.write_text(json.dumps([to_dict(item) for item in scenarios], indent=2, sort_keys=True) + "\n", encoding="utf-8")
    _serialize_result({"scenario_count": len(scenarios), "output_path": str(destination)})
    return 0


def cmd_physics_export_labels(args: argparse.Namespace) -> int:
    config, project_root, registry = _load_phase2_context(args)
    context, _ = initialize_run(
        config=config,
        config_path=str(Path(args.config).resolve()),
        command="physics-export-labels",
        project_root=project_root,
    )
    logger = configure_logger("gic.phase2.export", config["logging"]["level"], context.log_file)
    scenario_mode = args.scenario_mode or config["scenario"].get("type", "uniform_field")
    outputs, reports = _solve_physics_mode(
        config=config,
        project_root=project_root,
        registry=registry,
        scenario_mode=scenario_mode,
    )
    write_summary(context, {"status": "ok", "outputs": outputs, "reports": reports})
    logger.info("Exported physics labels for scenario mode %s", scenario_mode)
    _serialize_result({"run_id": context.run_id, "outputs": outputs, "reports": reports})
    return 0


def cmd_physics_validate_solution(args: argparse.Namespace) -> int:
    config, project_root, registry = _load_phase2_context(args)
    context, _ = initialize_run(
        config=config,
        config_path=str(Path(args.config).resolve()),
        command="physics-validate-solution",
        project_root=project_root,
    )
    logger = configure_logger("gic.phase2.validate", config["logging"]["level"], context.log_file)
    outputs, reports = _solve_physics_mode(
        config=config,
        project_root=project_root,
        registry=registry,
        scenario_mode="uniform_field",
    )
    summary = summarize_validation_results([reports[0]["physics_case"], *reports[0]["solutions"]])
    report_path = write_validation_report(summary, context.report_dir / "physics_validation_report.json")
    write_summary(context, {"status": "ok", "report_path": str(report_path), "outputs": outputs})
    logger.info("Physics validation report written to %s", report_path)
    _serialize_result({"run_id": context.run_id, "report_path": str(report_path), "summary": summary})
    return 0


def cmd_signal_validate_input(args: argparse.Namespace) -> int:
    config, project_root, registry = _load_phase3_context(args)
    dataset_name = _phase3_dataset_name(args, config)
    context, _ = initialize_run(
        config=config,
        config_path=str(Path(args.config).resolve()),
        command="signal-validate-input",
        project_root=project_root,
    )
    logger = configure_logger("gic.phase3.validate", config["logging"]["level"], context.log_file)
    sample = _phase3_signal_sample(config=config, project_root=project_root, registry=registry, dataset_name=dataset_name)
    sample_validation = validate_signal_sample(sample)
    summary = summarize_validation_results([sample_validation])
    report_path = write_validation_report(summary, context.report_dir / "signal_validation_report.json")
    write_summary(context, {"status": "ok" if sample_validation["ok"] else "failed", "dataset_name": dataset_name, "report_path": str(report_path)})
    logger.info("Signal input validation report written to %s", report_path)
    _serialize_result({
        "run_id": context.run_id,
        "dataset_name": dataset_name,
        "sample_id": sample.sample_id,
        "report_path": str(report_path),
        "summary": summary,
    })
    return 0 if sample_validation["ok"] else 1


def cmd_signal_run_frontend(args: argparse.Namespace) -> int:
    config, project_root, registry = _load_phase3_context(args)
    dataset_name = _phase3_dataset_name(args, config)
    method_names = _phase3_active_methods(args, config)[:1]
    context, _ = initialize_run(
        config=config,
        config_path=str(Path(args.config).resolve()),
        command="signal-run-frontend",
        project_root=project_root,
    )
    logger = configure_logger("gic.phase3.run", config["logging"]["level"], context.log_file)
    payload = _run_phase3_methods(
        config=config,
        project_root=project_root,
        registry=registry,
        dataset_name=dataset_name,
        method_names=method_names,
        export_results=True,
        build_report=False,
    )
    summary = summarize_validation_results(payload["validations"])
    write_summary(
        context,
        {
            "status": "ok" if summary["error_count"] == 0 else "failed",
            "dataset_name": dataset_name,
            "methods": method_names,
            "exports": payload["exports"],
        },
    )
    logger.info("Completed signal frontend run for %s", method_names[0])
    _serialize_result(
        {
            "run_id": context.run_id,
            "dataset_name": dataset_name,
            "sample_id": payload["sample"].sample_id,
            "methods": method_names,
            "exports": payload["exports"],
            "validation_summary": summary,
            "result": signal_to_dict(payload["results"][0]) if payload["results"] else None,
        }
    )
    return 0 if summary["error_count"] == 0 else 1


def cmd_signal_compare_frontends(args: argparse.Namespace) -> int:
    config, project_root, registry = _load_phase3_context(args)
    dataset_name = _phase3_dataset_name(args, config)
    method_names = _phase3_active_methods(args, config)
    context, _ = initialize_run(
        config=config,
        config_path=str(Path(args.config).resolve()),
        command="signal-compare-frontends",
        project_root=project_root,
    )
    logger = configure_logger("gic.phase3.compare", config["logging"]["level"], context.log_file)
    payload = _run_phase3_methods(
        config=config,
        project_root=project_root,
        registry=registry,
        dataset_name=dataset_name,
        method_names=method_names,
        export_results=True,
        build_report=True,
    )
    summary = summarize_validation_results(payload["validations"])
    comparison_report = payload["comparison_report"]
    write_summary(
        context,
        {
            "status": "ok" if summary["error_count"] == 0 else "failed",
            "dataset_name": dataset_name,
            "default_method": comparison_report.default_method if comparison_report else None,
            "comparison_path": payload["comparison_path"],
        },
    )
    logger.info("Completed signal frontend comparison across %d methods", len(method_names))
    _serialize_result(
        {
            "run_id": context.run_id,
            "dataset_name": dataset_name,
            "sample_id": payload["sample"].sample_id,
            "methods": method_names,
            "exports": payload["exports"],
            "comparison_path": payload["comparison_path"],
            "comparison_report": signal_to_dict(comparison_report) if comparison_report else None,
            "validation_summary": summary,
        }
    )
    return 0 if summary["error_count"] == 0 else 1


def cmd_signal_export_features(args: argparse.Namespace) -> int:
    config, project_root, registry = _load_phase3_context(args)
    dataset_name = _phase3_dataset_name(args, config)
    method_names = _phase3_active_methods(args, config)
    context, _ = initialize_run(
        config=config,
        config_path=str(Path(args.config).resolve()),
        command="signal-export-features",
        project_root=project_root,
    )
    logger = configure_logger("gic.phase3.export", config["logging"]["level"], context.log_file)
    payload = _run_phase3_methods(
        config=config,
        project_root=project_root,
        registry=registry,
        dataset_name=dataset_name,
        method_names=method_names,
        export_results=True,
        build_report=False,
    )
    summary = summarize_validation_results(payload["validations"])
    write_summary(context, {"status": "ok" if summary["error_count"] == 0 else "failed", "dataset_name": dataset_name, "exports": payload["exports"]})
    logger.info("Exported signal-ready assets for %d methods", len(method_names))
    _serialize_result(
        {
            "run_id": context.run_id,
            "dataset_name": dataset_name,
            "sample_id": payload["sample"].sample_id,
            "exports": payload["exports"],
            "validation_summary": summary,
        }
    )
    return 0 if summary["error_count"] == 0 else 1


def cmd_signal_build_report(args: argparse.Namespace) -> int:
    config, project_root, registry = _load_phase3_context(args)
    method_names = _phase3_active_methods(args, config)
    context, _ = initialize_run(
        config=config,
        config_path=str(Path(args.config).resolve()),
        command="signal-build-report",
        project_root=project_root,
    )
    logger = configure_logger("gic.phase3.report", config["logging"]["level"], context.log_file)

    if args.dataset_name:
        dataset_name = _phase3_dataset_name(args, config)
        payload = _run_phase3_methods(
            config=config,
            project_root=project_root,
            registry=registry,
            dataset_name=dataset_name,
            method_names=method_names,
            export_results=False,
            build_report=True,
        )
        summary = summarize_validation_results(payload["validations"])
        comparison_report = payload["comparison_report"]
        write_summary(
            context,
            {
                "status": "ok" if summary["error_count"] == 0 else "failed",
                "dataset_name": dataset_name,
                "comparison_path": payload["comparison_path"],
                "default_method": comparison_report.default_method if comparison_report else None,
            },
        )
        logger.info("Built single-dataset Phase 3 comparison report")
        _serialize_result(
            {
                "run_id": context.run_id,
                "dataset_name": dataset_name,
                "sample_id": payload["sample"].sample_id,
                "comparison_path": payload["comparison_path"],
                "comparison_report": signal_to_dict(comparison_report) if comparison_report else None,
                "validation_summary": summary,
            }
        )
        return 0 if summary["error_count"] == 0 else 1

    synthetic_dataset, real_event_datasets, promotion_policy = _phase3_benchmark_config(config)
    synthetic_payload = _run_phase3_methods(
        config=config,
        project_root=project_root,
        registry=registry,
        dataset_name=synthetic_dataset,
        method_names=method_names,
        export_results=False,
        build_report=True,
    )
    validations = list(synthetic_payload["validations"])
    real_reports: list[dict[str, Any]] = []
    for dataset_name in real_event_datasets:
        real_payload = _run_phase3_methods(
            config=config,
            project_root=project_root,
            registry=registry,
            dataset_name=dataset_name,
            method_names=method_names,
            export_results=False,
            build_report=True,
        )
        validations.extend(real_payload["validations"])
        dataset_record = registry.get_dataset(dataset_name)
        real_reports.append(
            {
                "dataset_name": dataset_name,
                "station_id": real_payload["sample"].sensor_id,
                "time_range": dataset_record.time_range,
                "report": signal_to_dict(real_payload["comparison_report"]) if real_payload["comparison_report"] else None,
            }
        )

    summary = summarize_validation_results(validations)
    comparison_priority = config.get("signal", {}).get("comparison", {}).get("default_method_priority", [])
    real_benchmark = _aggregate_real_benchmark(
        reports=real_reports,
        comparison_priority=[str(item) for item in comparison_priority],
        promotion_policy=promotion_policy,
    )
    benchmark_summary = {
        "default_for_training": synthetic_payload["comparison_report"].default_method if synthetic_payload["comparison_report"] else None,
        "default_for_real_event_benchmark": real_benchmark["default_method"],
        "promotion_status": real_benchmark["promotion_status"],
        "promotion_reason": real_benchmark["promotion_reason"],
        "synthetic_benchmark": signal_to_dict(synthetic_payload["comparison_report"]) if synthetic_payload["comparison_report"] else None,
        "real_event_benchmark": real_benchmark,
    }
    benchmark_path = context.report_dir / "signal_benchmark_summary.json"
    benchmark_path.write_text(json.dumps(benchmark_summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_summary(
        context,
        {
            "status": "ok" if summary["error_count"] == 0 else "failed",
            "comparison_path": synthetic_payload["comparison_path"],
            "benchmark_path": str(benchmark_path),
            "default_for_training": benchmark_summary["default_for_training"],
            "default_for_real_event_benchmark": benchmark_summary["default_for_real_event_benchmark"],
        },
    )
    logger.info("Built dual-benchmark Phase 3 report")
    _serialize_result(
        {
            "run_id": context.run_id,
            "synthetic_dataset": synthetic_dataset,
            "comparison_path": synthetic_payload["comparison_path"],
            "benchmark_path": str(benchmark_path),
            "comparison_report": signal_to_dict(synthetic_payload["comparison_report"]) if synthetic_payload["comparison_report"] else None,
            "benchmark_summary": benchmark_summary,
            "validation_summary": summary,
        }
    )
    return 0 if summary["error_count"] == 0 else 1


def _phase5_clone_config(config: dict[str, Any]) -> dict[str, Any]:
    return json.loads(json.dumps(config))


def _phase5_training_override(config: dict[str, Any], epochs: int | None) -> dict[str, Any]:
    if epochs is None:
        return config
    updated = _phase5_clone_config(config)
    training_cfg = dict(updated.get("training", {}))
    training_cfg["epochs"] = int(epochs)
    updated["training"] = training_cfg
    return updated


def _phase5_dataset_path(config: dict[str, Any], project_root: Path, override: str | None = None) -> Path:
    if isinstance(override, str) and override:
        return Path(override).resolve()
    graph_cfg = config.get("graph")
    if not isinstance(graph_cfg, dict):
        raise ValueError("Phase 5 config requires a graph section")
    dataset_path = graph_cfg.get("dataset_path")
    if not isinstance(dataset_path, str) or not dataset_path:
        raise ValueError("Phase 5 config requires graph.dataset_path")
    path = Path(dataset_path)
    return path.resolve() if path.is_absolute() else (project_root / path).resolve()


def _phase5_report_path(config: dict[str, Any], project_root: Path) -> Path:
    ablation_cfg = config.get("ablation", {})
    if not isinstance(ablation_cfg, dict):
        ablation_cfg = {}
    graph_cfg = config.get("graph", {})
    if not isinstance(graph_cfg, dict):
        graph_cfg = {}
    report_path = ablation_cfg.get("phase4_report_path") or graph_cfg.get("phase4_report_path")
    if not isinstance(report_path, str) or not report_path:
        raise ValueError("Phase 5 config requires ablation.phase4_report_path or graph.phase4_report_path")
    path = Path(report_path)
    return path.resolve() if path.is_absolute() else (project_root / path).resolve()


def _phase5_compare_split(config: dict[str, Any], override: str | None = None) -> str:
    if isinstance(override, str) and override:
        return override
    evaluation_cfg = config.get("evaluation", {})
    if not isinstance(evaluation_cfg, dict):
        evaluation_cfg = {}
    return str(evaluation_cfg.get("compare_split", "test"))


def _phase5_train_and_evaluate(
    *,
    config: dict[str, Any],
    dataset_path: str | Path,
    output_root: Path,
    split: str,
) -> dict[str, Any]:
    train_result = train_main_model(config=config, dataset_path=dataset_path, output_dir=output_root)
    evaluation = evaluate_main_model(
        config=config,
        dataset_path=dataset_path,
        checkpoint_path=train_result.checkpoint_path,
        split=split,
    )
    return {
        "training_result": train_result,
        "evaluation": evaluation,
        "checkpoint_path": train_result.checkpoint_path,
        "history_path": train_result.history_path,
    }


def cmd_train_main_model(args: argparse.Namespace) -> int:
    config, project_root = _load_phase5_context(args)
    config = _phase5_training_override(config, args.epochs)
    dataset_path = _phase5_dataset_path(config, project_root, args.dataset_path)
    if not dataset_path.exists():
        raise FileNotFoundError(f"Phase 5 graph-ready data missing: {dataset_path}")
    context, _ = initialize_run(
        config=config,
        config_path=str(Path(args.config).resolve()),
        command="train-main-model",
        project_root=project_root,
    )
    logger = configure_logger("gic.phase5.train", config["logging"]["level"], context.log_file)
    result = train_main_model(config=config, dataset_path=dataset_path, output_dir=context.artifact_dir)
    metrics_report_path = write_json_report(
        {
            "validation_metrics": result.validation_metrics,
            "validation_hotspot_metrics": result.validation_hotspot_metrics,
            "test_metrics": result.test_metrics,
            "test_hotspot_metrics": result.test_hotspot_metrics,
            "best_epoch": result.best_epoch,
            "input_dim": result.input_dim,
            "model_input_dims": result.model_input_dims,
            "feature_names": result.feature_names,
            "feature_summary": result.feature_summary,
            "signal_summary": result.signal_summary,
            "dataset_summary": result.dataset_summary,
            "train_example_count": result.train_example_count,
            "val_example_count": result.val_example_count,
            "test_example_count": result.test_example_count,
        },
        context.report_dir / "phase5_main_training_metrics.json",
    )
    write_summary(
        context,
        {
            "status": "ok",
            "checkpoint_path": result.checkpoint_path,
            "history_path": result.history_path,
            "metrics_report_path": str(metrics_report_path),
        },
    )
    logger.info("Trained Phase 5 main model on %s", dataset_path)
    _serialize_result(
        {
            "run_id": context.run_id,
            "dataset_path": str(dataset_path),
            "checkpoint_path": result.checkpoint_path,
            "history_path": result.history_path,
            "metrics_report_path": str(metrics_report_path),
            "best_epoch": result.best_epoch,
            "validation_metrics": result.validation_metrics,
            "validation_hotspot_metrics": result.validation_hotspot_metrics,
            "test_metrics": result.test_metrics,
            "test_hotspot_metrics": result.test_hotspot_metrics,
            "feature_summary": result.feature_summary,
            "signal_summary": result.signal_summary,
            "dataset_summary": result.dataset_summary,
        }
    )
    return 0


def cmd_eval_main_model(args: argparse.Namespace) -> int:
    config, project_root = _load_phase5_context(args)
    dataset_path = _phase5_dataset_path(config, project_root, args.dataset_path)
    if not dataset_path.exists():
        raise FileNotFoundError(f"Phase 5 graph-ready data missing: {dataset_path}")
    if not args.checkpoint:
        raise ValueError("eval-main-model requires --checkpoint")
    checkpoint_path = Path(args.checkpoint).resolve()
    if not checkpoint_path.exists():
        raise FileNotFoundError(f"Phase 5 checkpoint missing: {checkpoint_path}")
    split = _phase5_compare_split(config, args.split)
    context, _ = initialize_run(
        config=config,
        config_path=str(Path(args.config).resolve()),
        command="eval-main-model",
        project_root=project_root,
    )
    logger = configure_logger("gic.phase5.eval", config["logging"]["level"], context.log_file)
    payload = evaluate_main_model(config=config, dataset_path=dataset_path, checkpoint_path=checkpoint_path, split=split)
    predictions_path = write_json_report(payload["rows"], context.report_dir / f"phase5_{split}_predictions.json")
    metrics_path = write_json_report(payload["metrics"], context.report_dir / f"phase5_{split}_metrics.json")
    hotspot_path = write_json_report(payload["hotspot_metrics"], context.report_dir / f"phase5_{split}_hotspot_metrics.json")
    reconstruction_path = write_json_report(payload["reconstruction_maps"], context.report_dir / f"phase5_{split}_reconstruction_maps.json")
    case_studies_path = write_json_report(payload["case_studies"], context.report_dir / f"phase5_{split}_case_studies.json")
    write_summary(
        context,
        {
            "status": "ok",
            "split": split,
            "checkpoint_path": str(checkpoint_path),
            "predictions_path": str(predictions_path),
            "metrics_path": str(metrics_path),
            "hotspot_path": str(hotspot_path),
            "reconstruction_path": str(reconstruction_path),
            "case_studies_path": str(case_studies_path),
        },
    )
    logger.info("Evaluated Phase 5 main model on split %s", split)
    _serialize_result(
        {
            "run_id": context.run_id,
            "dataset_path": payload["dataset_path"],
            "checkpoint_path": str(checkpoint_path),
            "split": split,
            "predictions_path": str(predictions_path),
            "metrics_path": str(metrics_path),
            "hotspot_path": str(hotspot_path),
            "reconstruction_path": str(reconstruction_path),
            "case_studies_path": str(case_studies_path),
            "metrics": payload["metrics"],
            "hotspot_metrics": payload["hotspot_metrics"],
            "feature_summary": payload["feature_summary"],
            "signal_summary": payload["signal_summary"],
            "dataset_summary": payload["dataset_summary"],
        }
    )
    return 0


def cmd_export_main_predictions(args: argparse.Namespace) -> int:
    config, project_root = _load_phase5_context(args)
    dataset_path = _phase5_dataset_path(config, project_root, args.dataset_path)
    if not dataset_path.exists():
        raise FileNotFoundError(f"Phase 5 graph-ready data missing: {dataset_path}")
    if not args.checkpoint:
        raise ValueError("export-main-predictions requires --checkpoint")
    checkpoint_path = Path(args.checkpoint).resolve()
    if not checkpoint_path.exists():
        raise FileNotFoundError(f"Phase 5 checkpoint missing: {checkpoint_path}")
    split = _phase5_compare_split(config, args.split)
    context, _ = initialize_run(
        config=config,
        config_path=str(Path(args.config).resolve()),
        command="export-main-predictions",
        project_root=project_root,
    )
    logger = configure_logger("gic.phase5.export", config["logging"]["level"], context.log_file)
    payload = evaluate_main_model(config=config, dataset_path=dataset_path, checkpoint_path=checkpoint_path, split=split)
    predictions_path = write_json_report(payload["rows"], context.report_dir / f"phase5_{split}_predictions.json")
    write_summary(context, {"status": "ok", "predictions_path": str(predictions_path), "split": split})
    logger.info("Exported Phase 5 predictions for split %s", split)
    _serialize_result({"run_id": context.run_id, "split": split, "predictions_path": str(predictions_path)})
    return 0


def cmd_run_ablation(args: argparse.Namespace) -> int:
    config, project_root = _load_phase5_context(args)
    dataset_path = _phase5_dataset_path(config, project_root, args.dataset_path)
    if not dataset_path.exists():
        raise FileNotFoundError(f"Phase 5 graph-ready data missing: {dataset_path}")
    phase4_report_path = _phase5_report_path(config, project_root)
    if not phase4_report_path.exists():
        raise FileNotFoundError(f"Phase 4 comparison report missing: {phase4_report_path}")
    config = _phase5_clone_config(config)
    config.setdefault("ablation", {})["phase4_report_path"] = str(phase4_report_path)
    compare_split = _phase5_compare_split(config)
    context, _ = initialize_run(
        config=config,
        config_path=str(Path(args.config).resolve()),
        command="run-ablation",
        project_root=project_root,
    )
    logger = configure_logger("gic.phase5.ablation", config["logging"]["level"], context.log_file)
    payload = run_phase5_ablation_suite(
        base_config=config,
        base_config_path=str(Path(args.config).resolve()),
        dataset_path=dataset_path,
        output_root=context.artifact_dir / "ablations",
        compare_split=compare_split,
        project_root=project_root,
    )
    report_path = write_json_report(payload, context.report_dir / "phase5_ablation_report.json")
    write_summary(
        context,
        {
            "status": "ok",
            "report_path": str(report_path),
            "ablation_count": len(payload["ablations"]),
            "compare_split": compare_split,
        },
    )
    logger.info("Completed Phase 5 ablation suite")
    _serialize_result(
        {
            "run_id": context.run_id,
            "report_path": str(report_path),
            "ablation_count": len(payload["ablations"]),
            "comparison_with_phase4": payload["comparison_with_phase4"],
        }
    )
    return 0


def cmd_build_main_report(args: argparse.Namespace) -> int:
    config, project_root = _load_phase5_context(args)
    dataset_path = _phase5_dataset_path(config, project_root, args.dataset_path)
    if not dataset_path.exists():
        raise FileNotFoundError(f"Phase 5 graph-ready data missing: {dataset_path}")
    phase4_report_path = _phase5_report_path(config, project_root)
    if not phase4_report_path.exists():
        raise FileNotFoundError(f"Phase 4 comparison report missing: {phase4_report_path}")
    config = _phase5_clone_config(config)
    config.setdefault("ablation", {})["phase4_report_path"] = str(phase4_report_path)
    compare_split = _phase5_compare_split(config)
    context, _ = initialize_run(
        config=config,
        config_path=str(Path(args.config).resolve()),
        command="build-main-report",
        project_root=project_root,
    )
    logger = configure_logger("gic.phase5.report", config["logging"]["level"], context.log_file)
    default_run = _phase5_train_and_evaluate(
        config=config,
        dataset_path=dataset_path,
        output_root=ensure_directory(context.artifact_dir / "main_model_default"),
        split=compare_split,
    )
    default_eval = default_run["evaluation"]
    predictions_path = write_json_report(default_eval["rows"], context.report_dir / f"phase5_{compare_split}_predictions.json")
    metrics_path = write_json_report(default_eval["metrics"], context.report_dir / f"phase5_{compare_split}_metrics.json")
    hotspot_path = write_json_report(default_eval["hotspot_metrics"], context.report_dir / f"phase5_{compare_split}_hotspot_metrics.json")
    reconstruction_path = write_json_report(default_eval["reconstruction_maps"], context.report_dir / f"phase5_{compare_split}_reconstruction_maps.json")
    case_studies_path = write_json_report(default_eval["case_studies"], context.report_dir / f"phase5_{compare_split}_case_studies.json")
    ablation_payload = run_phase5_ablation_suite(
        base_config=config,
        base_config_path=str(Path(args.config).resolve()),
        dataset_path=dataset_path,
        output_root=context.artifact_dir / "ablations",
        compare_split=compare_split,
        project_root=project_root,
    )
    comparison_with_phase4 = compare_with_phase4_report(default_eval["metrics"], phase4_report_path)
    report_payload = {
        "dataset_name": Path(dataset_path).stem,
        "dataset_path": str(dataset_path),
        "compare_split": compare_split,
        "default_config_path": str(Path(args.config).resolve()),
        "phase4_report_path": str(phase4_report_path),
        "dataset_summary": default_eval["dataset_summary"],
        "default_run": {
            "checkpoint_path": default_run["checkpoint_path"],
            "history_path": default_run["history_path"],
            "metrics": default_eval["metrics"],
            "hotspot_metrics": default_eval["hotspot_metrics"],
            "feature_summary": default_eval["feature_summary"],
            "signal_summary": default_eval["signal_summary"],
            "predictions_path": str(predictions_path),
            "metrics_path": str(metrics_path),
            "hotspot_path": str(hotspot_path),
            "reconstruction_path": str(reconstruction_path),
            "case_studies_path": str(case_studies_path),
        },
        "ablations": ablation_payload["ablations"],
        "comparison_with_phase4": comparison_with_phase4,
    }
    report_path = write_json_report(report_payload, context.report_dir / "phase5_main_report.json")
    markdown_path = write_markdown_report(build_phase5_report_markdown(report_payload), context.report_dir / "phase5_main_report.md")
    write_summary(
        context,
        {
            "status": "ok",
            "report_path": str(report_path),
            "markdown_path": str(markdown_path),
            "ablation_count": len(ablation_payload["ablations"]),
            "phase5_beats_phase4_best": comparison_with_phase4["phase5_beats_phase4_best"],
        },
    )
    logger.info("Built Phase 5 main-model report")
    _serialize_result(
        {
            "run_id": context.run_id,
            "report_path": str(report_path),
            "markdown_path": str(markdown_path),
            "ablation_count": len(ablation_payload["ablations"]),
            "comparison_with_phase4": comparison_with_phase4,
        }
    )
    return 0

def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
