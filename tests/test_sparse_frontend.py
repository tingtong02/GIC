from __future__ import annotations

from gic.data.loaders.timeseries_loader import TimeSeriesLoader
from gic.data.registry import RegistryStore
from gic.signal.methods.sparse_frontend import SparseFrontend
from gic.signal.preprocess import build_signal_sample_from_timeseries
from gic.signal.schema import FrontendConfig


def test_sparse_frontend_dictionary_backend_runs(project_root) -> None:
    registry = RegistryStore(project_root=project_root, registry_root='data/registry')
    dataset = registry.get_dataset('sample_geomagnetic_storm_day')
    source = registry.get_source(dataset.source_name)
    series, _ = TimeSeriesLoader(project_root).load_geomagnetic(dataset, source)
    sample = build_signal_sample_from_timeseries(series, {'synthetic_noise': {'enabled': True, 'random_seed': 3}})
    result = SparseFrontend().run(
        sample,
        FrontendConfig(
            method_name='sparse_denoise',
            method_version='1.1',
            parameters={
                'backend': 'dictionary_lasso',
                'trend_window': 3,
                'refine_window': 3,
                'sparsity_lambda': 0.5,
                'n_dictionary_components': 4,
                'max_iter': 100,
                'random_seed': 5,
            },
        ),
    )
    assert result.method_name == 'sparse_denoise'
    assert result.metadata['backend'] == 'dictionary_lasso'


def test_sparse_frontend_legacy_backend_still_works(project_root) -> None:
    registry = RegistryStore(project_root=project_root, registry_root='data/registry')
    dataset = registry.get_dataset('sample_geomagnetic_storm_day')
    source = registry.get_source(dataset.source_name)
    series, _ = TimeSeriesLoader(project_root).load_geomagnetic(dataset, source)
    sample = build_signal_sample_from_timeseries(series, {'synthetic_noise': {'enabled': True}})
    result = SparseFrontend().run(
        sample,
        FrontendConfig(
            method_name='legacy_sparse_baseline',
            method_version='1.0',
            parameters={'backend': 'legacy_sparse_baseline', 'trend_window': 3, 'refine_window': 3},
        ),
    )
    assert result.metadata['backend'] == 'legacy_sparse_baseline'
