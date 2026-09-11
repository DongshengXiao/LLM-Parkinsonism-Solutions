from llm_parkinsonism.metrics import compute_metrics
from llm_parkinsonism.models import AcceptanceCriterion, GoalContract, TaskState


def test_token_efficiency_and_tail_metrics():
    c = GoalContract(
        goal="g",
        criteria=(AcceptanceCriterion("A", "a"), AcceptanceCriterion("B", "b")),
    )
    s = TaskState(
        verified={"A": True, "B": True},
        tokens=4000,
        useful_tokens=2000,
        executed_actions=4,
        unscoped_executed_actions=2,
        complexity_added=1.0,
        first_completion_tokens=3000,
    )
    m = compute_metrics(s, c, required_complexity=2.0)
    assert m.success == 1.0
    assert m.token_efficiency == 0.25
    assert m.useful_token_ratio == 0.5
    assert m.termination_overrun_ratio == 0.25
    assert m.goal_drift_rate == 0.5
    assert m.complexity_accretion_index == 0.5
    assert 0 <= m.llm_parkinsonism_index <= 100
