"""Minimal reproduction of the motivating watchdog scope-control example."""

from llm_parkinsonism.controller import GlobalExecutiveController
from llm_parkinsonism.models import (
    AcceptanceCriterion,
    ActionKind,
    ActionProposal,
    GoalContract,
    TaskState,
)


contract = GoalContract(
    goal="Independently alert when nodes A or B are down.",
    criteria=(
        AcceptanceCriterion("A_DOWN", "A down -> A NODE DOWN ALERT"),
        AcceptanceCriterion("B_DOWN", "B down -> B NODE DOWN ALERT"),
    ),
    non_goals=("SITE DOWN aggregation", "suppression of individual alerts"),
)

controller = GlobalExecutiveController(contract)
state = TaskState()

site_down = ActionProposal(
    action_id="site-correlation",
    description="Add SITE DOWN correlation and suppress individual node alerts",
    kind=ActionKind.OPTIONAL,
    target_criterion=None,
    expected_utility=0.2,
    token_cost=1800,
    complexity_delta=1.2,
    risk=0.15,
)

node_a = ActionProposal(
    action_id="test-a",
    description="Test A down -> A NODE DOWN ALERT",
    kind=ActionKind.REQUIRED,
    target_criterion="A_DOWN",
    expected_utility=0.5,
    token_cost=700,
    complexity_delta=0.05,
    risk=0.03,
)

print("SITE DOWN:", controller.evaluate_action(state, site_down))
print("A DOWN test:", controller.evaluate_action(state, node_a))
