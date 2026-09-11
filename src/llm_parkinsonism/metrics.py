from __future__ import annotations

from dataclasses import dataclass, asdict

from .models import GoalContract, TaskState


@dataclass(frozen=True)
class EpisodeMetrics:
    success: float
    verified_utility: float
    total_tokens: int
    useful_token_ratio: float
    token_efficiency: float
    nonproductive_persistence_ratio: float
    termination_overrun_ratio: float
    goal_drift_rate: float
    complexity_accretion_index: float
    llm_parkinsonism_index: float
    executed_actions: int
    rejected_actions: int

    def as_dict(self) -> dict:
        return asdict(self)


def compute_metrics(
    state: TaskState,
    contract: GoalContract,
    required_complexity: float,
) -> EpisodeMetrics:
    verified_utility = state.completion_fraction(contract)
    success = 1.0 if state.all_complete(contract) else 0.0
    total_tokens = max(state.tokens, 1)

    useful_ratio = min(max(state.useful_tokens / total_tokens, 0.0), 1.0)
    token_efficiency = 1000.0 * verified_utility / total_tokens
    nonproductive = 1.0 - useful_ratio

    if state.first_completion_tokens is None:
        termination_overrun = 0.0
    else:
        termination_overrun = max(total_tokens - state.first_completion_tokens, 0) / total_tokens

    goal_drift = (
        state.unscoped_executed_actions / state.executed_actions
        if state.executed_actions
        else 0.0
    )
    complexity_accretion = max(state.complexity_added, 0.0) / max(required_complexity, 1e-9)

    lpi = 100.0 * (
        0.35 * nonproductive
        + 0.30 * termination_overrun
        + 0.20 * goal_drift
        + 0.15 * min(complexity_accretion, 1.0)
    )
    lpi = min(max(lpi, 0.0), 100.0)

    return EpisodeMetrics(
        success=success,
        verified_utility=verified_utility,
        total_tokens=state.tokens,
        useful_token_ratio=useful_ratio,
        token_efficiency=token_efficiency,
        nonproductive_persistence_ratio=nonproductive,
        termination_overrun_ratio=termination_overrun,
        goal_drift_rate=goal_drift,
        complexity_accretion_index=complexity_accretion,
        llm_parkinsonism_index=lpi,
        executed_actions=state.executed_actions,
        rejected_actions=state.rejected_actions,
    )
