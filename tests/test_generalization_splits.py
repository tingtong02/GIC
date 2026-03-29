from gic.eval.generalization import GeneralizationSplitConfig, build_generalization_summary


def test_generalization_summary_groups_events() -> None:
    rows = [
        {'event_id': 'storm_2020_sep01', 'proxy_hidden_mae': 1.0, 'trend_correlation': 0.8, 'peak_timing_error_minutes': 5.0},
        {'event_id': 'storm_2020_oct01', 'proxy_hidden_mae': 2.0, 'trend_correlation': 0.6, 'peak_timing_error_minutes': 10.0},
    ]
    split = GeneralizationSplitConfig(
        main_event_ids=['storm_2020_sep01'],
        generalization_event_ids=['storm_2020_oct01'],
        boundary_event_ids=['storm_2020_nov01'],
    )
    summary = build_generalization_summary(rows, split)
    assert summary['group_counts']['main'] == 1
    assert summary['group_counts']['generalization'] == 1
    assert summary['grouped_metrics']['main']['mean_hidden_mae_proxy'] == 1.0
