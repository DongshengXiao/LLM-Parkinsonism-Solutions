from __future__ import annotations

from dataclasses import dataclass

from .models import (
    ActionKind,
    ActionProposal,
    Decision,
    DecisionType,
    GoalContract,
    TaskState,
)


@dataclass(frozen=True)
class ControllerConfig:
    """Tunable policy for Global Executive Control (GEC)."""

    token_budget: int = 40_000
    token_penalty_per_1k: float = 0.015
    complexity_tax: float = 0.08
    risk_tax: float = 0.05
    min_net_value: float = 0.0
    no_progress_limit: int = 3
    allow_optional_actions: bool = False


class GlobalExecutiveController:
    """A deterministic global gate layered above a proposal-generating LLM.

    The controller intentionally does *not* generate work. It enforces a frozen
    GoalContract, external verification, a marginal-value test, a complexity tax,
    a token budget, and three terminal states: success, economic stop, blocked.
    """

    def __init__(self, contract: GoalContract, config: ControllerConfig | None = None):
        self.contract = contract
        self.config = config or ControllerConfig()

    def preflight(self, state: TaskState) -> Decision:
        """Decide whether the loop is even allowed to request another action."""

        if state.all_complete(self.contract):
            return Decision(
                DecisionType.STOP_SUCCESS,
                "All frozen acceptance criteria have externally verified evidence.",
            )

        if state.tokens >= self.config.token_budget:
            return Decision(
                DecisionType.STOP_BLOCKED,
                "Token budget exhausted before all acceptance criteria were verified.",
            )

        if state.no_progress_streak >= self.config.no_progress_limit:
            return Decision(
                DecisionType.REPLAN,
                "No measurable goal progress for the configured number of cycles; "
                "local repair is suspended and global replanning is required.",
            )

        return Decision(DecisionType.CONTINUE, "Further work may be justified.")

    def evaluate_action(self, state: TaskState, proposal: ActionProposal) -> Decision:
        """Gate one candidate action against scope, marginal value, and complexity."""

        remaining_budget = self.config.token_budget - state.tokens
        if proposal.token_cost > remaining_budget:
            return Decision(
                DecisionType.STOP_BLOCKED,
                "The candidate action cannot fit within the remaining token budget.",
            )

        if proposal.target_criterion and state.is_verified(proposal.target_criterion):
            return Decision(
                DecisionType.REJECT,
                f"Criterion {proposal.target_criterion} is already verified; repeated work is unnecessary.",
            )

        if proposal.target_criterion is None:
            if proposal.kind == ActionKind.DELETE and proposal.complexity_delta < 0:
                pass
            elif not self.config.allow_optional_actions:
                return Decision(
                    DecisionType.REJECT,
                    "Action is not linked to any unmet frozen acceptance criterion; "
                    "it remains optional and cannot become a hard gate.",
                )

        if (
            proposal.target_criterion is not None
            and proposal.target_criterion not in self.contract.criterion_ids()
        ):
            return Decision(
                DecisionType.REJECT,
                "Action targets a self-invented requirement outside the GoalContract.",
            )

        token_penalty = self.config.token_penalty_per_1k * (proposal.token_cost / 1000.0)
        complexity_penalty = self.config.complexity_tax * max(proposal.complexity_delta, 0.0)
        risk_penalty = self.config.risk_tax * max(proposal.risk, 0.0)
        net_value = proposal.expected_utility - token_penalty - complexity_penalty - risk_penalty

        if net_value <= self.config.min_net_value:
            return Decision(
                DecisionType.STOP_ECONOMIC,
                "Expected marginal utility does not exceed token, complexity, and risk costs.",
                net_value=net_value,
            )

        return Decision(
            DecisionType.APPROVE,
            "Action is in-scope and has positive expected net value.",
            net_value=net_value,
        )
