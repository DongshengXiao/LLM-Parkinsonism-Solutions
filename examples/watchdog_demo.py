"""Minimal GEC v0.2 reproduction of the motivating watchdog scope-control example."""

from llm_parkinsonism.controller import GlobalExecutiveController
from llm_parkinsonism.models import (
    AcceptanceCriterion,
    ActionKind,
    ActionProposal,
    GoalContract,
    LinkType,
    ScopeAssessment,
    ScopeLink,
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

# The proposal generator misleadingly declares SITE DOWN as if it served A_DOWN.
# GEC does not trust that self-declared link; an independent scope assessment rules.
site_down = ActionProposal(
    action_id="site-correlation",
    description="Add SITE DOWN correlation and suppress individual node alerts",
    kind=ActionKind.OPTIONAL,
    token_cost=1800,
    complexity_delta=1.2,
    risk=0.15,
    success_probability=0.7,
    declared_links=(ScopeLink("A_DOWN", LinkType.DIRECT, 0.92),),
)
site_scope = ScopeAssessment(
    links=(ScopeLink(None, LinkType.FORBIDDEN, 0.99),),
    non_goal_match=True,
)

node_a = ActionProposal(
    action_id="test-a",
    description="Implement and verify A down -> A NODE DOWN ALERT",
    kind=ActionKind.REQUIRED,
    token_cost=700,
    complexity_delta=0.05,
    risk=0.03,
    success_probability=0.9,
)
node_a_scope = ScopeAssessment(
    links=(ScopeLink("A_DOWN", LinkType.DIRECT, 0.99),),
)

print("SITE DOWN:", controller.evaluate_action(state, site_down, site_scope))
print("A DOWN:", controller.evaluate_action(state, node_a, node_a_scope))
