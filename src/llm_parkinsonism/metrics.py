from __future__ import annotations

from dataclasses import asdict, dataclass

from .models import GoalContract, TaskState


@dataclass(frozen=True)
class EpisodeMetrics:
    success: float
    verified_utility: float
    total_tokens: int
    tokens_to_first_completion: float
    direct_useful_token_ratio: float
    process_useful_token_ratio: float
    token_efficiency: float
    termination_overrun_ratio: float
    precompletion_goal_drift_rate: float
    gross_complexity_accretion_index: float
    net_complexity_index: float
    executive_persistence_index: float
    executed_actions: int
    rejected_actions: int

    def as_dict(self) -> dict:
        return asdict(self)


def compute_metrics(state: TaskState, contract: GoalContract, required_complexity: float) -> EpisodeMetrics:
    # Evaluation uses the simulator's external world-state oracle, not the controller's self-report.
    verified_utility = state.world_completion_fraction(contract)
    success = 1.0 if state.world_all_complete(contract) else 0.0
    total_tokens_safe = max(state.tokens, 1)

    direct_ratio = min(max(state.direct_useful_tokens / total_tokens_safe, 0.0), 1.0)
    process_ratio = min(max(state.process_useful_tokens / total_tokens_safe, 0.0), 1.0)
    token_efficiency = 1000.0 * verified_utility / total_tokens_safe

    if state.first_completion_tokens is None:
        termination_overrun = 0.0
        tokens_to_completion = float("nan")
    else:
        termination_overrun = max(state.tokens - state.first_completion_tokens, 0) / total_tokens_safe
        tokens_to_completion = float(state.first_completion_tokens)

    pre_gdr = (
        state.precompletion_unscoped_actions / state.precompletion_executed_actions
        if state.precompletion_executed_actions
        else 0.0
    )
    gross_cai = state.gross_complexity_added / max(required_complexity, 1e-9)
    net_ci = max(state.net_complexity_delta, 0.0) / max(required_complexity, 1e-9)

    # Exploratory descriptive composite only; primary outcomes remain success and cost.
    nonproductive = 1.0 - process_ratio
    epi = 100.0 * (
        0.40 * nonproductive
        + 0.30 * termination_overrun
        + 0.20 * pre_gdr
        + 0.10 * min(gross_cai, 1.0)
    )
    epi = min(max(epi, 0.0), 100.0)

    return EpisodeMetrics(
        success=success,
        verified_utility=verified_utility,
        total_tokens=state.tokens,
        tokens_to_first_completion=tokens_to_completion,
        direct_useful_token_ratio=direct_ratio,
        process_useful_token_ratio=process_ratio,
        token_efficiency=token_efficiency,
        termination_overrun_ratio=termination_overrun,
        precompletion_goal_drift_rate=pre_gdr,
        gross_complexity_accretion_index=gross_cai,
        net_complexity_index=net_ci,
        executive_persistence_index=epi,
        executed_actions=state.executed_actions,
        rejected_actions=state.rejected_actions,
    )
