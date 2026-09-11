from llm_parkinsonism.controller import ControllerConfig, GlobalExecutiveController
from llm_parkinsonism.models import (
    AcceptanceCriterion,
    ActionKind,
    ActionProposal,
    DecisionType,
    Evidence,
    GoalContract,
    TaskState,
)


def contract():
    return GoalContract(
        goal="Alert A and B independently",
        criteria=(
            AcceptanceCriterion("A", "A down alert"),
            AcceptanceCriterion("B", "B down alert"),
        ),
        non_goals=("SITE DOWN aggregation",),
    )


def test_success_stop_requires_all_frozen_criteria():
    c = contract()
    state = TaskState(
        verified={"A": True, "B": True},
        evidence={
            "A": Evidence("A", True, "external"),
            "B": Evidence("B", True, "external"),
        },
    )
    decision = GlobalExecutiveController(c).preflight(state)
    assert decision.decision == DecisionType.STOP_SUCCESS


def test_rejects_unscoped_optional_work():
    c = contract()
    proposal = ActionProposal(
        action_id="x",
        description="Add SITE DOWN correlation",
        kind=ActionKind.OPTIONAL,
        target_criterion=None,
        expected_utility=0.4,
        token_cost=1000,
        complexity_delta=1.0,
    )
    decision = GlobalExecutiveController(c).evaluate_action(TaskState(), proposal)
    assert decision.decision == DecisionType.REJECT


def test_rejects_self_invented_requirement():
    c = contract()
    proposal = ActionProposal(
        action_id="x",
        description="Implement invented criterion C",
        kind=ActionKind.REQUIRED,
        target_criterion="C",
        expected_utility=0.5,
        token_cost=500,
    )
    decision = GlobalExecutiveController(c).evaluate_action(TaskState(), proposal)
    assert decision.decision == DecisionType.REJECT


def test_approves_positive_value_required_action():
    c = contract()
    proposal = ActionProposal(
        action_id="x",
        description="Test A down",
        kind=ActionKind.REQUIRED,
        target_criterion="A",
        expected_utility=0.4,
        token_cost=900,
        complexity_delta=0.05,
        risk=0.05,
    )
    decision = GlobalExecutiveController(c).evaluate_action(TaskState(), proposal)
    assert decision.decision == DecisionType.APPROVE
    assert decision.net_value is not None and decision.net_value > 0


def test_economic_stop_on_negative_net_value():
    c = contract()
    proposal = ActionProposal(
        action_id="x",
        description="Very expensive in-scope action",
        kind=ActionKind.REQUIRED,
        target_criterion="A",
        expected_utility=0.001,
        token_cost=10_000,
        complexity_delta=1.0,
        risk=1.0,
    )
    cfg = ControllerConfig(token_budget=50_000)
    decision = GlobalExecutiveController(c, cfg).evaluate_action(TaskState(), proposal)
    assert decision.decision == DecisionType.STOP_ECONOMIC


def test_no_progress_triggers_replan():
    c = contract()
    state = TaskState(no_progress_streak=3)
    decision = GlobalExecutiveController(c).preflight(state)
    assert decision.decision == DecisionType.REPLAN
