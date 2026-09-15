from llm_parkinsonism.metrics import compute_metrics
from llm_parkinsonism.models import AcceptanceCriterion, Evidence, GoalContract, TaskState


def test_metrics_separate_precompletion_drift_and_tail():
    c = GoalContract(goal="g", criteria=(AcceptanceCriterion("A", "a"), AcceptanceCriterion("B", "b")))
    s = TaskState(
        world_satisfied={"A", "B"},
        evidence={"A": Evidence("A", True, "external"), "B": Evidence("B", True, "external")},
        tokens=4000,
        direct_useful_tokens=1800,
        process_useful_tokens=2400,
        precompletion_executed_actions=4,
        precompletion_unscoped_actions=1,
        gross_complexity_added=2.0,
        net_complexity_delta=0.5,
        first_completion_tokens=3000,
    )
    m = compute_metrics(s, c, required_complexity=2.0)
    assert m.success == 1.0
    assert m.token_efficiency == 0.25
    assert m.termination_overrun_ratio == 0.25
    assert m.precompletion_goal_drift_rate == 0.25
    assert m.gross_complexity_accretion_index == 1.0
    assert m.net_complexity_index == 0.25
    assert 0 <= m.executive_persistence_index <= 100
