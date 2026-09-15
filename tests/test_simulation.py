from llm_parkinsonism.simulation import SCENARIOS, make_exogenous_stream, run_episode, run_soft_value_probe


def test_matched_stream_is_policy_independent():
    s = SCENARIOS[0]
    a = make_exogenous_stream(s, seed=42)
    b = make_exogenous_stream(s, seed=42)
    assert [e.proposal.action_id for e in a] == [e.proposal.action_id for e in b]
    assert [e.proposal.description for e in a] == [e.proposal.description for e in b]


def test_gec_can_complete_without_postcompletion_tail():
    m, ep = run_episode(SCENARIOS[0], "gec", seed=17)
    assert m.total_tokens > 0
    if m.success == 1.0:
        assert m.termination_overrun_ratio == 0.0


def test_all_policies_obey_hard_token_ceiling():
    for p in ("baseline", "budget_only", "gec"):
        m, _ = run_episode(SCENARIOS[0], p, seed=19, token_budget=5000)
        assert m.total_tokens <= 5000


def test_soft_probe_rejects_bad_candidate_without_stopping_good_one():
    out = run_soft_value_probe()
    assert out["good"] == "approve"
    assert out["bad"] == "reject"
    assert out["terminal"] == "continue"
