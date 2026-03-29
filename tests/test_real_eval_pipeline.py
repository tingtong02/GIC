from gic.eval.real_pipeline import build_real_failure_cases
from gic.eval.reports import build_phase7_report_markdown
from gic.eval.trustworthiness import build_trustworthiness_summary


def test_real_failure_case_selection_prefers_large_peak_errors() -> None:
    payload = {
        'rows': [
            {'event_id': 'a', 'peak_timing_error_minutes': 5.0, 'trend_correlation': 0.8},
            {'event_id': 'b', 'peak_timing_error_minutes': 20.0, 'trend_correlation': 0.2},
        ]
    }
    cases = build_real_failure_cases(payload, top_k=1)
    assert len(cases) == 1
    assert cases[0]['event_id'] == 'b'


def test_phase7_markdown_report_contains_decision() -> None:
    report = {
        'event_set_name': 'demo',
        'event_asset_count': 3,
        'result_row_count': 9,
        'failure_case_count': 1,
        'default_promotion_decision': 'no_real_default_promotion',
        'evidence_summary': {'level_counts': {'level_3': 3}},
        'generalization_summary': {'group_counts': {'main': 1}},
        'robustness_summary': {'row_count': 2},
        'trustworthiness_summary': build_trustworthiness_summary({'default_promotion_decision': 'no_real_default_promotion', 'failure_case_count': 1, 'evidence_summary': {'level_counts': {'level_3': 3}}}),
    }
    markdown = build_phase7_report_markdown(report)
    assert 'Phase 7 Real Event Validation Report' in markdown
    assert 'no_real_default_promotion' in markdown
