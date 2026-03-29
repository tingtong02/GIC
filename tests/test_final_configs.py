from __future__ import annotations

from pathlib import Path

from gic.config import load_config
from gic.reports import collect_final_versions


ROOT = Path(__file__).resolve().parents[1]
FINAL_CONFIGS = [
    ROOT / 'configs/final/final_default.yaml',
    ROOT / 'configs/final/final_reproduction.yaml',
    ROOT / 'configs/final/final_real_eval.yaml',
    ROOT / 'configs/final/final_with_kg.yaml',
    ROOT / 'configs/final/final_without_kg.yaml',
]


def test_final_configs_load_and_reference_frozen_assets() -> None:
    for config_path in FINAL_CONFIGS:
        config = load_config(config_path)
        assert config['project']['stage'] == 'phase_8'
        versions = collect_final_versions(ROOT, config)
        assets = versions['assets']
        assert Path(assets['synthetic_dataset_path']).exists()
        assert Path(assets['phase5_report_path']).exists()
        assert Path(assets['phase6_report_path']).exists()
        assert Path(assets['phase7_report_path']).exists()


def test_final_default_variant_flags_are_frozen() -> None:
    default_config = load_config(ROOT / 'configs/final/final_default.yaml')
    with_kg_config = load_config(ROOT / 'configs/final/final_with_kg.yaml')
    without_kg_config = load_config(ROOT / 'configs/final/final_without_kg.yaml')
    assert default_config['final']['default_variant'] == 'without_kg'
    assert with_kg_config['final']['default_variant'] == 'with_kg'
    assert without_kg_config['final']['default_variant'] == 'without_kg'
