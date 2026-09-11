from llm_parkinsonism.simulation import SCENARIOS, run_episode


def test_gec_finishes_watchdog_without_post_completion_tail():
    metrics, episode = run_episode(SCENARIOS[0], "gec", seed=17)
    assert metrics.success == 1.0
    assert metrics.termination_overrun_ratio == 0.0
    assert episode["stop_reason"] == "success"


def test_baseline_is_allowed_to_generate_tail_work():
    metrics, _ = run_episode(SCENARIOS[0], "baseline", seed=19)
    assert metrics.success == 1.0
    assert metrics.total_tokens > 0
