from __future__ import annotations

import json
from pathlib import Path

from gic.cli.main import main
from gic.config import load_config


ROOT = Path(__file__).resolve().parents[1]
PHASE0_CONFIG = ROOT / 'configs/phase0/phase0_dev.yaml'
PHASE1_CONFIG = ROOT / 'configs/phase1/phase1_dev.yaml'
PHASE3_CONFIG = ROOT / 'configs/phase3/phase3_dev.yaml'
PHASE4_CONFIG = ROOT / 'configs/phase4/phase4_dev.yaml'


def _write_phase4_test_config(tmp_path: Path, *, train_epochs: int = 3, report_epochs: int = 2) -> Path:
    config = load_config(PHASE4_CONFIG)
    config['training']['epochs'] = train_epochs
    config['training']['batch_size'] = 4
    config['reporting']['training_epochs'] = report_epochs
    config_path = tmp_path / 'phase4_test_config.json'
    config_path.write_text(json.dumps(config, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    return config_path


def test_show_config_outputs_json(capsys) -> None:
    exit_code = main(['show-config', '--config', str(PHASE0_CONFIG)])
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert exit_code == 0
    assert payload['project']['stage'] == 'phase_0'


def test_validate_env_outputs_summary(capsys) -> None:
    exit_code = main(['validate-env'])
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert exit_code == 0
    assert 'python_version' in payload


def test_run_creates_summary(tmp_path: Path, capsys) -> None:
    exit_code = main(
        [
            'run',
            '--config',
            str(PHASE0_CONFIG),
            '--project-root',
            str(tmp_path),
        ]
    )
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    summary_path = Path(payload['summary_path'])
    assert exit_code == 0
    assert summary_path.exists()
    assert 'Phase 0 dry run completed' in captured.err


def test_data_list_sources_outputs_registry(capsys) -> None:
    exit_code = main(['data-list-sources', '--config', str(PHASE1_CONFIG)])
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert exit_code == 0
    assert any(item['source_name'] == 'matpower_case118' for item in payload['sources'])


def test_data_convert_sample_writes_interim_outputs(capsys) -> None:
    exit_code = main(
        [
            'data-convert-sample',
            '--config',
            str(PHASE1_CONFIG),
            '--project-root',
            str(ROOT),
        ]
    )
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert exit_code == 0
    assert payload['manifest_count'] >= 2


def test_signal_validate_input_outputs_report(capsys) -> None:
    exit_code = main(
        [
            'signal-validate-input',
            '--config',
            str(PHASE3_CONFIG),
            '--project-root',
            str(ROOT),
        ]
    )
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert exit_code == 0
    assert Path(payload['report_path']).exists()


def test_signal_compare_frontends_outputs_default_method(capsys) -> None:
    exit_code = main(
        [
            'signal-compare-frontends',
            '--config',
            str(PHASE3_CONFIG),
            '--project-root',
            str(ROOT),
        ]
    )
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert exit_code == 0
    assert payload['comparison_report']['default_method'] in {
        'raw_baseline',
        'lowfreq_baseline',
        'fastica',
        'sparse_denoise',
    }
    assert payload['comparison_report']['default_scope'] == 'training'


def test_signal_build_report_outputs_dual_benchmark_summary(capsys) -> None:
    exit_code = main(
        [
            'signal-build-report',
            '--config',
            str(PHASE3_CONFIG),
            '--project-root',
            str(ROOT),
        ]
    )
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    real_benchmark = payload['benchmark_summary']['real_event_benchmark']
    assert exit_code == 0
    assert payload['benchmark_summary']['default_for_training'] in {
        'raw_baseline',
        'lowfreq_baseline',
        'fastica',
        'sparse_denoise',
    }
    assert real_benchmark['observed_station_count'] == 3
    assert real_benchmark['observed_event_window_count'] == 3
    assert real_benchmark['observed_dataset_count'] == 9
    assert real_benchmark['policy_agreement_count'] in {0, 2}
    assert set(real_benchmark['policy_leaders']) == {'mean_score', 'window_wins'}
    if real_benchmark['policy_leaders']['mean_score'] == real_benchmark['policy_leaders']['window_wins']:
        assert payload['benchmark_summary']['promotion_status'] == 'ready'
    else:
        assert payload['benchmark_summary']['promotion_status'] == 'provisional'


def test_graph_build_samples_outputs_counts(capsys) -> None:
    exit_code = main(
        [
            'graph-build-samples',
            '--config',
            str(PHASE4_CONFIG),
            '--project-root',
            str(ROOT),
        ]
    )
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert exit_code == 0
    assert payload['graph_count'] == 5
    assert payload['node_count'] == 3
    assert payload['edge_count'] >= 6
    assert Path(payload['graph_report_path']).exists()


def test_graph_export_dataset_writes_graph_ready_assets(capsys) -> None:
    exit_code = main(
        [
            'graph-export-dataset',
            '--config',
            str(PHASE4_CONFIG),
            '--project-root',
            str(ROOT),
        ]
    )
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert exit_code == 0
    assert Path(payload['manifest_path']).exists()
    assert Path(payload['dataset_path']).exists()
    assert payload['graph_count'] == 5


def test_graph_build_report_writes_baseline_comparison(tmp_path: Path, capsys) -> None:
    config_path = _write_phase4_test_config(tmp_path, train_epochs=2, report_epochs=2)
    exit_code = main(
        [
            'graph-build-report',
            '--config',
            str(config_path),
            '--project-root',
            str(ROOT),
        ]
    )
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert exit_code == 0
    assert Path(payload['report_path']).exists()
    assert Path(payload['markdown_path']).exists()
    assert payload['comparison']['default_graph_baseline'] in {'gcn', 'graphsage', 'gat'}
    assert payload['ablation_counts']['sparsity'] == 6
    assert payload['ablation_counts']['features'] == 4


def test_train_baseline_outputs_checkpoint_for_gcn(tmp_path: Path, capsys) -> None:
    config_path = _write_phase4_test_config(tmp_path, train_epochs=3, report_epochs=2)
    exit_code = main(
        [
            'train-baseline',
            '--config',
            str(config_path),
            '--project-root',
            str(ROOT),
            '--model-type',
            'gcn',
            '--dataset-path',
            str(ROOT / 'data/processed/graph_ready/datasets/timeseries_case118_graph_default.json'),
        ]
    )
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert exit_code == 0
    assert Path(payload['checkpoint_path']).exists()
    assert Path(payload['history_path']).exists()


def test_eval_baseline_outputs_metrics_predictions_and_reconstruction(tmp_path: Path, capsys) -> None:
    config_path = _write_phase4_test_config(tmp_path, train_epochs=3, report_epochs=2)
    train_exit = main(
        [
            'train-baseline',
            '--config',
            str(config_path),
            '--project-root',
            str(ROOT),
            '--model-type',
            'gcn',
            '--dataset-path',
            str(ROOT / 'data/processed/graph_ready/datasets/timeseries_case118_graph_default.json'),
        ]
    )
    train_captured = capsys.readouterr()
    train_payload = json.loads(train_captured.out)
    assert train_exit == 0

    eval_exit = main(
        [
            'eval-baseline',
            '--config',
            str(config_path),
            '--project-root',
            str(ROOT),
            '--model-type',
            'gcn',
            '--dataset-path',
            str(ROOT / 'data/processed/graph_ready/datasets/timeseries_case118_graph_default.json'),
            '--checkpoint',
            train_payload['checkpoint_path'],
            '--split',
            'test',
        ]
    )
    eval_captured = capsys.readouterr()
    eval_payload = json.loads(eval_captured.out)
    assert eval_exit == 0
    assert Path(eval_payload['predictions_path']).exists()
    assert Path(eval_payload['metrics_path']).exists()
    assert Path(eval_payload['reconstruction_path']).exists()
    assert eval_payload['metrics']['overall']['mae'] >= 0.0
