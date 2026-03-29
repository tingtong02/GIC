from gic.eval.evidence import ValidationEvidenceBundle, build_evidence_summary


def test_evidence_bundle_exposes_applicable_metric_groups() -> None:
    bundle = ValidationEvidenceBundle(
        event_id='storm_2020_sep01',
        available_truth_types=['geomagnetic_station_series'],
        direct_measurements=[],
        indirect_references=['station_magnetic_disturbance'],
        trend_reference=True,
        peak_reference=True,
        ranking_reference=True,
        limitations=['no_gic_truth'],
        default_level=3,
    )
    assert bundle.descriptor() == 'event_trend_peak_reference'
    assert bundle.applicable_metric_groups() == ['trend', 'peak', 'ranking']


def test_evidence_summary_counts_levels() -> None:
    bundles = [
        ValidationEvidenceBundle('a', [], [], [], True, True, True, default_level=3),
        ValidationEvidenceBundle('b', [], [], [], True, False, False, default_level=4),
    ]
    summary = build_evidence_summary(bundles)
    assert summary['bundle_count'] == 2
    assert summary['level_counts']['level_3'] == 1
    assert summary['level_counts']['level_4'] == 1
