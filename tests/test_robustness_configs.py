from gic.eval.robustness import RobustnessScenarioConfig, build_robustness_summary


def test_robustness_summary_preserves_rows() -> None:
    scenario = RobustnessScenarioConfig(sensor_dropout=[0.3, 0.7], timing_shift_minutes=[-10, 10], noise_stress_std=[0.0])
    rows = [{'scenario': 'sensor_dropout', 'parameter': 0.3}]
    summary = build_robustness_summary(rows, scenario)
    assert summary['row_count'] == 1
    assert summary['scenario']['sensor_dropout'] == [0.3, 0.7]
