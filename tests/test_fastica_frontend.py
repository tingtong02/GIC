from __future__ import annotations

from gic.data.loaders.timeseries_loader import TimeSeriesLoader
from gic.data.registry import RegistryStore
from gic.signal.methods.fastica_frontend import FastICAFrontend
from gic.signal.preprocess import build_signal_sample_from_timeseries
from gic.signal.schema import FrontendConfig


def test_fastica_frontend_runs_on_multichannel_fixture(project_root) -> None:
    registry = RegistryStore(project_root=project_root, registry_root='data/registry')
    dataset = registry.get_dataset('sample_geomagnetic_storm_day')
    source = registry.get_source(dataset.source_name)
    series, _ = TimeSeriesLoader(project_root).load_geomagnetic(dataset, source)
    sample = build_signal_sample_from_timeseries(
        series,
        {
            'synthetic_noise': {
                'enabled': True,
                'gaussian_std': 1.0,
                'sinusoid_amplitude': 3.0,
                'sinusoid_cycles': 2.0,
                'reference_lowfreq_window': 3,
                'random_seed': 9,
            }
        },
    )
    frontend = FastICAFrontend()
    result = frontend.run(
        sample,
        FrontendConfig(
            method_name='fastica',
            method_version='1.1',
            parameters={
                'backend': 'sklearn_fastica',
                'n_components': 3,
                'max_iter': 100,
                'tol': 1e-4,
                'selection_window': 3,
                'quasi_window': 3,
            },
        ),
    )
    assert result.method_name == 'fastica'
    assert result.metadata['backend'] == 'sklearn_fastica'
    assert len(result.quasi_dc_series.time_index) == len(sample.time_index)
