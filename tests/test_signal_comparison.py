from __future__ import annotations

from gic.data.loaders.timeseries_loader import TimeSeriesLoader
from gic.data.registry import RegistryStore
from gic.signal.comparison import build_comparison_report
from gic.signal.methods.lowfreq_frontend import LowFrequencyFrontend
from gic.signal.methods.raw_baseline import RawBaselineFrontend
from gic.signal.preprocess import build_signal_sample_from_timeseries
from gic.signal.schema import FrontendConfig


def test_comparison_report_ranks_synthetic_methods(project_root) -> None:
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
                'sinusoid_amplitude': 4.0,
                'sinusoid_cycles': 1.0,
                'reference_lowfreq_window': 3,
                'random_seed': 11,
            }
        },
    )
    raw_result = RawBaselineFrontend().run(sample, FrontendConfig('raw_baseline', '1.0', {}))
    lowfreq_result = LowFrequencyFrontend().run(sample, FrontendConfig('lowfreq_baseline', '1.0', {'smoothing_window': 3}))
    report = build_comparison_report(
        sample_id=sample.sample_id,
        results=[raw_result, lowfreq_result],
        comparison_config={
            'default_method_priority': ['lowfreq_baseline', 'raw_baseline'],
            'synthetic_score_policy': {'quasi_dc_correlation': 3.0, 'correlation_to_reference': 2.0},
        },
    )
    assert report.default_scope == 'training'
    assert report.benchmark_type == 'synthetic'
    assert report.default_method in {'lowfreq_baseline', 'raw_baseline'}
    assert len(report.summary_table) == 2


def test_comparison_report_marks_real_event_scope(project_root) -> None:
    registry = RegistryStore(project_root=project_root, registry_root='data/registry')
    dataset = registry.get_dataset('intermagnet_bou_2020_sep01_smoke')
    source = registry.get_source(dataset.source_name)
    series, _ = TimeSeriesLoader(project_root).load_geomagnetic(dataset, source)
    sample = build_signal_sample_from_timeseries(series, {'synthetic_noise': {'enabled': True}})
    raw_result = RawBaselineFrontend().run(sample, FrontendConfig('raw_baseline', '1.0', {}))
    lowfreq_result = LowFrequencyFrontend().run(sample, FrontendConfig('lowfreq_baseline', '1.0', {'smoothing_window': 5}))
    report = build_comparison_report(
        sample_id=sample.sample_id,
        results=[raw_result, lowfreq_result],
        comparison_config={
            'default_method_priority': ['lowfreq_baseline', 'raw_baseline'],
            'real_data_score_policy': {
                'trend_alignment_to_observed': 2.0,
                'denoised_observed_correlation': 1.0,
                'peak_preservation_ratio': 1.0,
                'stability_score': 1.0,
            },
        },
    )
    assert report.benchmark_type == 'real_event'
    assert report.default_scope == 'real_event_benchmark'
    assert report.promotion_status == 'provisional'
