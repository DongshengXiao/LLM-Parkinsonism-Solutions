from __future__ import annotations

import csv
import json
import math
import random
import statistics
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from .controller import ControllerConfig, GlobalExecutiveController
from .metrics import EpisodeMetrics, compute_metrics
from .models import (
    AcceptanceCriterion,
    ActionKind,
    ActionProposal,
    DecisionType,
    Evidence,
    GoalContract,
    TaskState,
)


@dataclass(frozen=True)
class Scenario:
    name: str
    goal: str
    criteria: tuple[str, ...]
    non_goals: tuple[str, ...]
    action_token_mean: int
    action_token_sd: int
    required_complexity: float
    success_probability: float = 0.90

    def contract(self) -> GoalContract:
        return GoalContract(
            goal=self.goal,
            criteria=tuple(
                AcceptanceCriterion(f"R{i+1}", text, 1.0)
                for i, text in enumerate(self.criteria)
            ),
            non_goals=self.non_goals,
        )


SCENARIOS: tuple[Scenario, ...] = (
    Scenario(
        name="watchdog",
        goal="Independently alert when disaster-recovery nodes A or B become unavailable.",
        criteria=(
            "A unavailable produces A NODE DOWN ALERT.",
            "B unavailable produces B NODE DOWN ALERT.",
            "A and B unavailable leaves both node-level alerts observable.",
            "Recovery restores the correct healthy state.",
        ),
        non_goals=(
            "SITE DOWN correlation",
            "suppression of individual node alerts",
            "cross-node inference",
        ),
        action_token_mean=900,
        action_token_sd=180,
        required_complexity=4.0,
    ),
    Scenario(
        name="api_release",
        goal="Release a service API with health, authentication, and rollback verified.",
        criteria=(
            "Health endpoint passes.",
            "Authentication rejects invalid credentials and accepts valid credentials.",
            "Rollback restores the previous stable release.",
        ),
        non_goals=("new API gateway abstraction", "service mesh migration"),
        action_token_mean=1100,
        action_token_sd=250,
        required_complexity=3.0,
    ),
    Scenario(
        name="database_migration",
        goal="Migrate a schema without data loss and verify forward and rollback paths.",
        criteria=(
            "Forward migration completes.",
            "Record counts and checksums match expected values.",
            "Rollback restores the pre-migration schema and data.",
        ),
        non_goals=("ORM replacement", "unrelated index redesign"),
        action_token_mean=1250,
        action_token_sd=280,
        required_complexity=3.0,
    ),
    Scenario(
        name="ci_pipeline",
        goal="Create a CI pipeline that tests, builds, and publishes on the intended branch.",
        criteria=(
            "Unit tests run and fail the pipeline on test failure.",
            "Build artifact is reproducibly created.",
            "Publish step runs only on the intended branch after tests pass.",
        ),
        non_goals=("multi-cloud deployment", "repository-wide formatter migration"),
        action_token_mean=850,
        action_token_sd=170,
        required_complexity=3.0,
    ),
    Scenario(
        name="backup_restore",
        goal="Verify a backup can be created, integrity-checked, and restored.",
        criteria=(
            "Backup artifact is created.",
            "Integrity check passes.",
            "Restore recreates the expected files and metadata.",
        ),
        non_goals=("new archival tier", "cross-region replication redesign"),
        action_token_mean=1000,
        action_token_sd=220,
        required_complexity=3.0,
    ),
    Scenario(
        name="research_pipeline",
        goal="Produce a reproducible analysis with data validation, model run, and exported results.",
        criteria=(
            "Input data validation passes.",
            "Configured analysis completes reproducibly.",
            "Primary metrics are exported with provenance.",
        ),
        non_goals=("new model family", "dashboard redesign", "extra exploratory endpoints"),
        action_token_mean=1050,
        action_token_sd=240,
        required_complexity=3.0,
    ),
)


OPTIONAL_ACTIONS = (
    "Add an aggregation abstraction not required by the goal.",
    "Refactor naming and interfaces beyond acceptance criteria.",
    "Add a synthetic test for an optional behavior.",
    "Introduce a fallback layer for an unobserved edge case.",
    "Add monitoring for a newly invented subsystem.",
    "Generalize the implementation to a broader deployment topology.",
)

REPAIR_ACTIONS = (
    "Repair an optional abstraction introduced earlier.",
    "Debug a synthetic test for a non-required behavior.",
    "Resolve a dependency introduced by an optional refactor.",
)


class ProposalGenerator:
    """Stochastic local-next-step generator shared by all governance conditions."""

    def __init__(self, rng: random.Random, optional_probability: float = 0.28):
        self.rng = rng
        self.optional_probability = optional_probability
        self.counter = 0

    def _cost(self, scenario: Scenario, scale: float = 1.0) -> int:
        return max(
            100,
            int(self.rng.gauss(scenario.action_token_mean * scale, scenario.action_token_sd)),
        )

    def propose(
        self,
        state: TaskState,
        contract: GoalContract,
        scenario: Scenario,
        *,
        force_required: bool = False,
    ) -> ActionProposal:
        self.counter += 1
        unmet = list(state.unmet(contract))

        if state.maintenance_debt > 0 and not force_required and self.rng.random() < 0.55:
            return ActionProposal(
                action_id=f"A{self.counter}",
                description=self.rng.choice(REPAIR_ACTIONS),
                kind=ActionKind.REPAIR,
                target_criterion=None,
                expected_utility=0.03,
                token_cost=self._cost(scenario, 0.75),
                complexity_delta=-0.15,
                risk=0.05,
            )

        choose_optional = (
            not force_required
            and self.rng.random() < self.optional_probability
        )

        if unmet and not choose_optional:
            target = self.rng.choice(unmet)
            return ActionProposal(
                action_id=f"A{self.counter}",
                description=f"Implement or verify {target}: {next(c.description for c in contract.criteria if c.criterion_id == target)}",
                kind=ActionKind.REQUIRED,
                target_criterion=target,
                expected_utility=0.38,
                token_cost=self._cost(scenario),
                complexity_delta=0.05,
                risk=0.08,
            )

        return ActionProposal(
            action_id=f"A{self.counter}",
            description=self.rng.choice(OPTIONAL_ACTIONS),
            kind=ActionKind.OPTIONAL,
            target_criterion=None,
            expected_utility=0.04,
            token_cost=self._cost(scenario, 0.85),
            complexity_delta=self.rng.uniform(0.25, 0.80),
            risk=self.rng.uniform(0.05, 0.18),
        )


def _execute(
    rng: random.Random,
    state: TaskState,
    proposal: ActionProposal,
    scenario: Scenario,
    contract: GoalContract,
    planning_tokens: int,
) -> bool:
    """Execute one approved action. Returns whether verified utility increased."""

    before = state.completion_fraction(contract)
    state.tokens += proposal.token_cost
    state.executed_actions += 1
    state.complexity_added += proposal.complexity_delta

    if proposal.target_criterion is None:
        state.unscoped_executed_actions += 1
        if proposal.kind == ActionKind.OPTIONAL and rng.random() < 0.62:
            state.maintenance_debt += 1
        elif proposal.kind == ActionKind.REPAIR and state.maintenance_debt > 0:
            state.maintenance_debt -= 1
    else:
        if rng.random() < scenario.success_probability:
            state.verified[proposal.target_criterion] = True
            state.evidence[proposal.target_criterion] = Evidence(
                criterion_id=proposal.target_criterion,
                passed=True,
                source="simulated_external_verifier",
                details="Benchmark oracle observed the specified world-state condition.",
            )

    after = state.completion_fraction(contract)
    progressed = after > before

    if progressed:
        state.useful_tokens += planning_tokens + proposal.token_cost
        state.no_progress_streak = 0
    else:
        state.no_progress_streak += 1

    if state.all_complete(contract) and state.first_completion_tokens is None:
        state.first_completion_tokens = state.tokens

    return progressed


def run_episode(
    scenario: Scenario,
    policy: str,
    seed: int,
    *,
    token_budget: int = 40_000,
    max_cycles: int = 60,
    planning_tokens: int = 120,
    baseline_stop_probability: float = 0.12,
    optional_probability: float = 0.28,
) -> tuple[EpisodeMetrics, dict]:
    """Run one controlled synthetic episode."""

    if policy not in {"baseline", "budget_only", "gec"}:
        raise ValueError(f"Unknown policy: {policy}")

    rng = random.Random(seed)
    contract = scenario.contract()
    state = TaskState()
    generator = ProposalGenerator(rng, optional_probability=optional_probability)
    controller = GlobalExecutiveController(
        contract,
        ControllerConfig(token_budget=token_budget),
    )
    force_required = False
    trace: list[dict] = []

    for cycle in range(max_cycles):
        if policy == "gec":
            pre = controller.preflight(state)
            trace.append({"cycle": cycle, "phase": "preflight", "decision": pre.decision.value, "reason": pre.reason})
            if pre.decision == DecisionType.STOP_SUCCESS:
                state.stop_reason = "success"
                break
            if pre.decision == DecisionType.STOP_BLOCKED:
                state.stop_reason = "blocked"
                break
            if pre.decision == DecisionType.REPLAN:
                state.tokens += planning_tokens
                state.no_progress_streak = 0
                force_required = True
                trace.append({"cycle": cycle, "phase": "replan", "tokens": planning_tokens})
                continue
        else:
            if policy == "budget_only" and state.tokens >= token_budget:
                state.stop_reason = "budget"
                break
            if state.all_complete(contract) and rng.random() < baseline_stop_probability:
                state.stop_reason = "probabilistic_success_stop"
                break

        state.tokens += planning_tokens
        proposal = generator.propose(
            state,
            contract,
            scenario,
            force_required=force_required,
        )
        force_required = False
        trace.append({
            "cycle": cycle,
            "phase": "proposal",
            "action_id": proposal.action_id,
            "kind": proposal.kind.value,
            "target": proposal.target_criterion,
            "token_cost": proposal.token_cost,
            "complexity_delta": round(proposal.complexity_delta, 4),
        })

        if policy == "budget_only" and state.tokens + proposal.token_cost > token_budget:
            state.stop_reason = "budget"
            trace.append({"cycle": cycle, "phase": "budget_gate", "decision": "stop", "reason": "candidate would exceed remaining token budget"})
            break

        if policy == "gec":
            decision = controller.evaluate_action(state, proposal)
            trace.append({"cycle": cycle, "phase": "gate", "decision": decision.decision.value, "reason": decision.reason, "net_value": decision.net_value})
            if decision.decision == DecisionType.REJECT:
                state.rejected_actions += 1
                state.no_progress_streak += 1
                force_required = True
                continue
            if decision.decision in {DecisionType.STOP_BLOCKED, DecisionType.STOP_ECONOMIC}:
                state.stop_reason = decision.decision.value
                break
            if decision.decision != DecisionType.APPROVE:
                raise RuntimeError(f"Unexpected GEC decision: {decision.decision}")

        _execute(rng, state, proposal, scenario, contract, planning_tokens)
        trace.append({
            "cycle": cycle,
            "phase": "state",
            "completion": state.completion_fraction(contract),
            "tokens": state.tokens,
            "complexity_added": round(state.complexity_added, 4),
            "maintenance_debt": state.maintenance_debt,
        })

    else:
        state.stop_reason = "max_cycles"

    metrics = compute_metrics(state, contract, scenario.required_complexity)
    episode = {
        "scenario": scenario.name,
        "policy": policy,
        "seed": seed,
        "stop_reason": state.stop_reason,
        "metrics": metrics.as_dict(),
        "trace": trace,
    }
    return metrics, episode


def _mean_ci(values: Iterable[float]) -> tuple[float, float]:
    vals = list(values)
    if not vals:
        return 0.0, 0.0
    mean = statistics.fmean(vals)
    if len(vals) < 2:
        return mean, 0.0
    se = statistics.stdev(vals) / math.sqrt(len(vals))
    return mean, 1.96 * se


def run_benchmark(
    output_dir: str | Path,
    *,
    episodes_per_scenario: int = 1000,
    seed: int = 20260911,
) -> list[dict]:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    policies = ("baseline", "budget_only", "gec")
    rows: list[dict] = []
    trace_examples: list[dict] = []
    all_policy_metrics: dict[str, list[EpisodeMetrics]] = {p: [] for p in policies}

    for s_idx, scenario in enumerate(SCENARIOS):
        for p_idx, policy in enumerate(policies):
            episode_metrics: list[EpisodeMetrics] = []
            for i in range(episodes_per_scenario):
                episode_seed = seed + s_idx * 100_000 + p_idx * 10_000 + i
                metrics, episode = run_episode(scenario, policy, episode_seed)
                episode_metrics.append(metrics)
                all_policy_metrics[policy].append(metrics)
                if i == 0:
                    trace_examples.append(episode)

            fields = EpisodeMetrics.__dataclass_fields__.keys()
            row = {"scenario": scenario.name, "policy": policy, "n": episodes_per_scenario}
            for field in fields:
                values = [float(getattr(m, field)) for m in episode_metrics]
                mean, ci = _mean_ci(values)
                row[f"{field}_mean"] = mean
                row[f"{field}_ci95"] = ci
            rows.append(row)

    summary_path = output_dir / "results_summary.csv"
    with summary_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    with (output_dir / "example_trajectories.json").open("w", encoding="utf-8") as fh:
        json.dump(trace_examples, fh, indent=2)

    aggregate: list[dict] = []
    metric_names = list(EpisodeMetrics.__dataclass_fields__.keys())
    for policy in policies:
        metrics_for_policy = all_policy_metrics[policy]
        out = {"policy": policy, "scenarios": len(SCENARIOS), "episodes": len(metrics_for_policy)}
        for metric in metric_names:
            vals = [float(getattr(m, metric)) for m in metrics_for_policy]
            mean, ci = _mean_ci(vals)
            out[metric] = mean
            out[f"{metric}_ci95"] = ci
        aggregate.append(out)

    with (output_dir / "aggregate_results.json").open("w", encoding="utf-8") as fh:
        json.dump(aggregate, fh, indent=2)

    with (output_dir / "aggregate_results.csv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(aggregate[0].keys()))
        writer.writeheader()
        writer.writerows(aggregate)

    return aggregate
