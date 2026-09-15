from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .models import (
    ActionProposal,
    Decision,
    DecisionType,
    GoalContract,
    LinkType,
    ScopeAssessment,
    TaskState,
)


@dataclass(frozen=True)
class ControllerConfig:
    """Tunable policy for Global Executive Control (GEC)."""

    token_budget: int = 40_000
    token_penalty_per_1k: float = 0.015
    complexity_tax: float = 0.08
    risk_tax: float = 0.05
    verification_tax: float = 0.01
    min_net_value: float = 0.0
    no_progress_limit: int = 3
    scope_confidence_threshold: float = 0.80
    evidence_confidence_threshold: float = 0.95
    prerequisite_discount: float = 0.55
    risk_mitigation_discount: float = 0.35
    soft_utility_beta: float = 0.25
    enable_scope_gate: bool = True
    enable_value_gate: bool = True
    enable_progress_breaker: bool = True


class GlobalExecutiveController:
    """Auditable governance layer above a proposal-generating model.

    Key design rule: rejecting one poor candidate never implies that the project as
    a whole should stop. Economic stopping is a *state-level* decision after hard
    requirements are complete and no candidate in an independently assessed set
    has positive continuation value.
    """

    def __init__(self, contract: GoalContract, config: ControllerConfig | None = None):
        self.contract = contract
        self.config = config or ControllerConfig()

    def preflight(self, state: TaskState) -> Decision:
        if state.tokens >= self.config.token_budget:
            return Decision(
                DecisionType.STOP_BUDGET,
                "Token budget exhausted.",
            )

        if state.all_complete(self.contract) and not self.contract.soft_criteria:
            return Decision(
                DecisionType.STOP_SUCCESS,
                "All hard acceptance criteria carry valid external evidence.",
            )

        if (
            self.config.enable_progress_breaker
            and state.no_progress_streak >= self.config.no_progress_limit
        ):
            return Decision(
                DecisionType.REPLAN,
                "No criterion, prerequisite, or externally grounded process progress "
                "for the configured number of cycles; global replanning is required.",
            )

        if state.all_complete(self.contract):
            return Decision(
                DecisionType.CONTINUE,
                "Hard requirements are complete; only governed soft-objective work may continue.",
            )

        return Decision(DecisionType.CONTINUE, "Hard requirements remain unmet.")

    def _eligible_links(self, state: TaskState, assessment: ScopeAssessment):
        links = []
        for link in assessment.links:
            if link.confidence < self.config.scope_confidence_threshold:
                continue
            if link.link_type in {LinkType.NONE, LinkType.FORBIDDEN}:
                continue
            if link.target_id is None:
                continue
            if link.target_id not in self.contract.criterion_ids():
                continue
            if link.link_type in {LinkType.DIRECT, LinkType.VERIFICATION} and state.is_verified(link.target_id):
                continue
            links.append(link)
        return links

    def expected_utility(self, state: TaskState, proposal: ActionProposal, assessment: ScopeAssessment) -> float:
        """Contract-aligned expected verified utility, not generator self-scoring."""

        value = 0.0
        for link in self._eligible_links(state, assessment):
            criterion = self.contract.get_criterion(link.target_id)  # type: ignore[arg-type]
            if link.target_id in self.contract.hard_ids():
                base = criterion.weight / self.contract.total_weight
            else:
                base = self.config.soft_utility_beta * criterion.weight / self.contract.total_soft_weight

            if link.link_type in {LinkType.DIRECT, LinkType.VERIFICATION, LinkType.SOFT}:
                multiplier = 1.0
            elif link.link_type == LinkType.PREREQUISITE:
                multiplier = self.config.prerequisite_discount
            elif link.link_type == LinkType.RISK_MITIGATION:
                multiplier = self.config.risk_mitigation_discount
            else:
                multiplier = 0.0

            value = max(value, proposal.success_probability * base * multiplier * link.confidence)
        return value

    def evaluate_action(
        self,
        state: TaskState,
        proposal: ActionProposal,
        assessment: ScopeAssessment,
    ) -> Decision:
        remaining_budget = self.config.token_budget - state.tokens
        if proposal.token_cost > remaining_budget:
            return Decision(
                DecisionType.REJECT,
                "Candidate cannot fit within the remaining token budget; reject and replan.",
            )

        if self.config.enable_scope_gate:
            if assessment.non_goal_match or any(
                link.link_type == LinkType.FORBIDDEN
                and link.confidence >= self.config.scope_confidence_threshold
                for link in assessment.links
            ):
                return Decision(
                    DecisionType.REJECT,
                    "Independent scope assessment matches an explicit non-goal.",
                )

            eligible = self._eligible_links(state, assessment)
            if not eligible:
                return Decision(
                    DecisionType.REJECT,
                    "No sufficiently confident direct, prerequisite, verification, risk-mitigation, "
                    "or soft-objective link to the governed Goal Contract.",
                )

        expected_utility = self.expected_utility(state, proposal, assessment)
        token_penalty = self.config.token_penalty_per_1k * (proposal.token_cost / 1000.0)
        complexity_penalty = self.config.complexity_tax * max(proposal.complexity_delta, 0.0)
        risk_penalty = self.config.risk_tax * max(proposal.risk, 0.0)
        verification_penalty = self.config.verification_tax if proposal.kind.value == "verify" else 0.0
        net_value = expected_utility - token_penalty - complexity_penalty - risk_penalty - verification_penalty

        if self.config.enable_value_gate and net_value <= self.config.min_net_value:
            return Decision(
                DecisionType.REJECT,
                "This candidate has non-positive expected net value; reject it without declaring the project finished.",
                net_value=net_value,
                expected_utility=expected_utility,
            )

        return Decision(
            DecisionType.APPROVE,
            "Candidate is governed in-scope and has acceptable expected net value.",
            net_value=net_value,
            expected_utility=expected_utility,
        )

    def classify_after_candidate_set(
        self,
        state: TaskState,
        decisions: Iterable[Decision],
        *,
        feasible_hard_path_exists: bool = True,
    ) -> Decision:
        """State-level terminal classifier after a candidate set / replan pass."""

        decisions = tuple(decisions)
        if state.all_complete(self.contract):
            if state.all_soft_complete(self.contract):
                return Decision(DecisionType.STOP_SUCCESS, "Hard and soft governed objectives are complete.")
            positive = any(d.decision == DecisionType.APPROVE and (d.net_value or 0.0) > self.config.min_net_value for d in decisions)
            if not positive:
                return Decision(
                    DecisionType.STOP_ECONOMIC,
                    "Hard requirements are complete and no candidate in the governed continuation set has positive net value.",
                )
            return Decision(DecisionType.CONTINUE, "At least one governed soft-objective action remains worthwhile.")

        if not feasible_hard_path_exists:
            return Decision(
                DecisionType.STOP_BLOCKED,
                "Hard requirements remain unmet and no feasible governed path to completion is available.",
            )

        if state.tokens >= self.config.token_budget:
            return Decision(DecisionType.STOP_BUDGET, "Budget exhausted before hard completion.")

        return Decision(DecisionType.CONTINUE, "A feasible path to hard completion remains.")
