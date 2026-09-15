from __future__ import annotations
import csv
import json
import math
import random
import statistics
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Iterable, Optional
from .controller import ControllerConfig, GlobalExecutiveController
from .metrics import EpisodeMetrics, compute_metrics
from .models import AcceptanceCriterion, ActionKind, ActionProposal, Decision, DecisionType, Evidence, GoalContract, LinkType, ScopeAssessment, ScopeLink, TaskState

@dataclass(frozen=True)
class Scenario:
    name: str
    goal: str
    criteria: tuple[str, ...]
    non_goals: tuple[str, ...]
    action_token_mean: int
    action_token_sd: int
    required_complexity: float
    prerequisite_indices: tuple[int, ...] = ()
    success_probability: float = 0.9

    def contract(self, *, include_soft: bool=False) -> GoalContract:
        soft = (AcceptanceCriterion('S1', 'Optional low-cost diagnostic summary with provenance', 0.5),) if include_soft else ()
        return GoalContract(goal=self.goal, criteria=tuple((AcceptanceCriterion(f'R{i + 1}', text, 1.0) for i, text in enumerate(self.criteria))), soft_criteria=soft, non_goals=self.non_goals)

    def prerequisite_targets(self) -> set[str]:
        return {f'R{i + 1}' for i in self.prerequisite_indices}
SCENARIOS: tuple[Scenario, ...] = (Scenario(name='watchdog', goal='Independently alert when disaster-recovery nodes A or B become unavailable.', criteria=('A unavailable produces A NODE DOWN ALERT.', 'B unavailable produces B NODE DOWN ALERT.', 'A and B unavailable leaves both node-level alerts observable.', 'Recovery restores the correct healthy state.'), non_goals=('SITE DOWN correlation', 'suppression of individual node alerts', 'cross-node inference'), action_token_mean=900, action_token_sd=180, required_complexity=4.0, prerequisite_indices=(2,)), Scenario(name='api_release', goal='Release a service API with health, authentication, and rollback verified.', criteria=('Health endpoint passes.', 'Authentication rejects invalid credentials and accepts valid credentials.', 'Rollback restores the previous stable release.'), non_goals=('new API gateway abstraction', 'service mesh migration'), action_token_mean=1100, action_token_sd=250, required_complexity=3.0, prerequisite_indices=(2,)), Scenario(name='database_migration', goal='Migrate a schema without data loss and verify forward and rollback paths.', criteria=('Forward migration completes.', 'Record counts and checksums match expected values.', 'Rollback restores the pre-migration schema and data.'), non_goals=('ORM replacement', 'unrelated index redesign'), action_token_mean=1250, action_token_sd=280, required_complexity=3.0, prerequisite_indices=(0, 2)), Scenario(name='ci_pipeline', goal='Create a CI pipeline that tests, builds, and publishes on the intended branch.', criteria=('Unit tests run and fail the pipeline on test failure.', 'Build artifact is reproducibly created.', 'Publish step runs only on the intended branch after tests pass.'), non_goals=('multi-cloud deployment', 'repository-wide formatter migration'), action_token_mean=850, action_token_sd=170, required_complexity=3.0, prerequisite_indices=(2,)), Scenario(name='backup_restore', goal='Verify a backup can be created, integrity-checked, and restored.', criteria=('Backup artifact is created.', 'Integrity check passes.', 'Restore recreates the expected files and metadata.'), non_goals=('new archival tier', 'cross-region replication redesign'), action_token_mean=1000, action_token_sd=220, required_complexity=3.0, prerequisite_indices=(2,)), Scenario(name='research_pipeline', goal='Produce a reproducible analysis with data validation, model run, and exported results.', criteria=('Input data validation passes.', 'Configured analysis completes reproducibly.', 'Primary metrics are exported with provenance.'), non_goals=('new model family', 'dashboard redesign', 'extra exploratory endpoints'), action_token_mean=1050, action_token_sd=240, required_complexity=3.0, prerequisite_indices=(1,)))
OPTIONAL_ACTIONS = ('Add an aggregation abstraction not required by the goal.', 'Refactor naming and interfaces beyond acceptance criteria.', 'Add a synthetic test for an optional behavior.', 'Introduce a fallback layer for an unobserved edge case.', 'Add monitoring for a newly invented subsystem.', 'Generalize the implementation to a broader deployment topology.')
REPAIR_ACTIONS = ('Repair an optional abstraction introduced earlier.', 'Debug a synthetic test for a non-required behavior.', 'Resolve a dependency introduced by an optional refactor.')

@dataclass(frozen=True)
class CandidateEvent:
    proposal: ActionProposal
    true_assessment: ScopeAssessment
    execution_draw: float
    verifier_draw: float
    stop_draw: float
    debt_draw: float
    invalidation_draw: float

def _cost(rng: random.Random, scenario: Scenario, scale: float=1.0) -> int:
    return max(100, int(rng.gauss(scenario.action_token_mean * scale, scenario.action_token_sd)))

def make_exogenous_stream(scenario: Scenario, seed: int, *, max_cycles: int=60, optional_probability: float=0.28, soft_probability: float=0.0, misleading_declaration_probability: float=0.35) -> list[CandidateEvent]:
    """Pre-generate policy-independent candidate and outcome opportunities.

    Every governance condition receives the same candidate stream and random draws.
    Policy choices determine only which candidates are executed and when the policy stops.
    """
    rng = random.Random(seed)
    hard_ids = [f'R{i + 1}' for i in range(len(scenario.criteria))]
    prereq_targets = scenario.prerequisite_targets()
    events: list[CandidateEvent] = []
    for i in range(max_cycles):
        u = rng.random()
        if soft_probability > 0 and u < soft_probability:
            link = ScopeLink('S1', LinkType.SOFT, 0.99)
            proposal = ActionProposal(action_id=f'E{i + 1}', description='Produce the governed soft diagnostic summary.', kind=ActionKind.SOFT, token_cost=_cost(rng, scenario, 0.35), complexity_delta=0.02, risk=0.01, success_probability=0.95, declared_links=(link,))
            assessment = ScopeAssessment((link,))
        elif u < soft_probability + optional_probability:
            forbidden = rng.random() < 0.45
            description = rng.choice(OPTIONAL_ACTIONS)
            true_link = ScopeLink(None, LinkType.FORBIDDEN if forbidden else LinkType.NONE, 0.99)
            if rng.random() < misleading_declaration_probability:
                declared = (ScopeLink(rng.choice(hard_ids), LinkType.DIRECT, 0.92),)
            else:
                declared = (true_link,)
            proposal = ActionProposal(action_id=f'E{i + 1}', description=description, kind=ActionKind.OPTIONAL, token_cost=_cost(rng, scenario, 0.85), complexity_delta=rng.uniform(0.25, 0.8), risk=rng.uniform(0.05, 0.18), success_probability=0.0, declared_links=declared, affected_criteria=(rng.choice(hard_ids),) if rng.random() < 0.08 else ())
            assessment = ScopeAssessment((true_link,), non_goal_match=forbidden)
        else:
            target = rng.choice(hard_ids)
            branch = rng.random()
            if branch < 0.1:
                link_type = LinkType.VERIFICATION
                kind = ActionKind.VERIFY
                scale = 2.6
                description = f'Run an expensive low-yield verification pass for {target}.'
                success_probability = 0.15
                risk = 0.1
            elif target in prereq_targets and branch < 0.42:
                link_type = LinkType.PREREQUISITE
                kind = ActionKind.PREREQUISITE
                scale = 0.55
                description = f'Prepare a validated prerequisite for {target}.'
                success_probability = scenario.success_probability
                risk = 0.03
            elif branch < 0.58:
                link_type = LinkType.VERIFICATION
                kind = ActionKind.VERIFY
                scale = 0.45
                description = f'Independently verify {target}.'
                success_probability = scenario.success_probability
                risk = 0.03
            else:
                link_type = LinkType.DIRECT
                kind = ActionKind.REQUIRED
                scale = 1.0
                description = f'Implement the governed requirement {target}.'
                success_probability = scenario.success_probability
                risk = 0.08
            true_link = ScopeLink(target, link_type, 0.99)
            declared = (true_link,)
            proposal = ActionProposal(action_id=f'E{i + 1}', description=description, kind=kind, token_cost=_cost(rng, scenario, scale), complexity_delta=0.05 if kind == ActionKind.REQUIRED else 0.01, risk=risk, success_probability=success_probability, declared_links=declared)
            assessment = ScopeAssessment((true_link,))
        events.append(CandidateEvent(proposal=proposal, true_assessment=assessment, execution_draw=rng.random(), verifier_draw=rng.random(), stop_draw=rng.random(), debt_draw=rng.random(), invalidation_draw=rng.random()))
    return events

def make_candidate_sets(scenario: Scenario, seed: int, *, max_cycles: int=60, batch_size: int=3, optional_probability: float=0.28, soft_probability: float=0.0) -> list[tuple[CandidateEvent, ...]]:
    """Matched exogenous candidate sets shared by every governance condition."""
    flat = make_exogenous_stream(scenario, seed, max_cycles=max_cycles * batch_size, optional_probability=optional_probability, soft_probability=soft_probability)
    return [tuple(flat[i:i + batch_size]) for i in range(0, len(flat), batch_size)]

def noisy_scope_assessment(event: CandidateEvent, contract: GoalContract, *, false_negative_rate: float=0.0, false_positive_rate: float=0.0) -> ScopeAssessment:
    """Deterministic noise injection based on event-specific random draws."""
    truth = event.true_assessment
    if truth.non_goal_match or any((l.link_type in {LinkType.NONE, LinkType.FORBIDDEN} for l in truth.links)):
        if event.verifier_draw < false_positive_rate:
            target = contract.hard_ids()[int(event.execution_draw * len(contract.hard_ids())) % len(contract.hard_ids())]
            return ScopeAssessment((ScopeLink(target, LinkType.DIRECT, 0.9),), source='noisy_scope_linker')
        return truth
    if event.verifier_draw < false_negative_rate:
        return ScopeAssessment((ScopeLink(None, LinkType.NONE, 0.95),), source='noisy_scope_linker')
    return truth

def _write_evidence(state: TaskState, criterion_id: str, *, passed_truth: bool, verifier_draw: float, verifier_false_positive_rate: float, verifier_false_negative_rate: float) -> bool:
    observed_pass = passed_truth
    if passed_truth and verifier_draw < verifier_false_negative_rate:
        observed_pass = False
    elif not passed_truth and verifier_draw < verifier_false_positive_rate:
        observed_pass = True
    state.evidence[criterion_id] = Evidence(criterion_id=criterion_id, passed=observed_pass, source='independent_external_verifier', state_version=state.world_version, confidence=0.99, valid=True, details='Synthetic verifier result; oracle truth is stored separately for evaluation.')
    return observed_pass

def _execute_event(state: TaskState, event: CandidateEvent, scenario: Scenario, contract: GoalContract, assessment: ScopeAssessment, *, planning_tokens: int, verifier_false_positive_rate: float=0.0, verifier_false_negative_rate: float=0.0, evidence_invalidation_rate: float=0.05) -> tuple[bool, bool, bool]:
    """Execute one action. Returns (direct_progress, process_progress, in_scope)."""
    proposal = event.proposal
    was_world_complete = state.world_all_complete(contract)
    before_world = state.world_completion_fraction(contract)
    before_verified = state.completion_fraction(contract)
    state.tokens += proposal.token_cost
    state.executed_actions += 1
    state.world_version += 1
    state.gross_complexity_added += max(proposal.complexity_delta, 0.0)
    state.net_complexity_delta += proposal.complexity_delta
    true_links = tuple((l for l in event.true_assessment.links if l.link_type not in {LinkType.NONE, LinkType.FORBIDDEN}))
    in_scope = bool(true_links) and (not event.true_assessment.non_goal_match)
    if not was_world_complete:
        state.precompletion_executed_actions += 1
        if not in_scope:
            state.precompletion_unscoped_actions += 1
    else:
        state.postcompletion_executed_actions += 1
    if not in_scope:
        if proposal.kind == ActionKind.OPTIONAL and event.debt_draw < 0.62:
            state.maintenance_debt += 1
        elif proposal.kind == ActionKind.REPAIR and state.maintenance_debt > 0:
            state.maintenance_debt -= 1
        if proposal.affected_criteria and event.invalidation_draw < evidence_invalidation_rate:
            state.invalidate_evidence(proposal.affected_criteria)
    process_progress = False
    for link in true_links:
        target = link.target_id
        if target is None:
            continue
        if link.link_type == LinkType.PREREQUISITE:
            if event.execution_draw < proposal.success_probability:
                state.validated_prerequisites.add(target)
                process_progress = True
        elif link.link_type == LinkType.VERIFICATION:
            truth = target in state.world_satisfied
            before = state.is_verified(target)
            observed = _write_evidence(state, target, passed_truth=truth, verifier_draw=event.verifier_draw, verifier_false_positive_rate=verifier_false_positive_rate, verifier_false_negative_rate=verifier_false_negative_rate)
            process_progress = process_progress or (observed and (not before))
        elif link.link_type in {LinkType.DIRECT, LinkType.SOFT}:
            prereq_ok = target not in scenario.prerequisite_targets() or target in state.validated_prerequisites
            truth_success = prereq_ok and event.execution_draw < proposal.success_probability
            if truth_success:
                state.world_satisfied.add(target)
            _write_evidence(state, target, passed_truth=truth_success or target in state.world_satisfied, verifier_draw=event.verifier_draw, verifier_false_positive_rate=verifier_false_positive_rate, verifier_false_negative_rate=verifier_false_negative_rate)
            process_progress = process_progress or truth_success
        elif link.link_type == LinkType.RISK_MITIGATION:
            process_progress = process_progress or event.execution_draw < proposal.success_probability
    after_world = state.world_completion_fraction(contract)
    after_verified = state.completion_fraction(contract)
    direct_progress = after_world > before_world
    evidence_progress = after_verified > before_verified
    process_progress = process_progress or evidence_progress
    if direct_progress:
        state.direct_useful_tokens += planning_tokens + proposal.token_cost
    if direct_progress or process_progress:
        state.process_useful_tokens += planning_tokens + proposal.token_cost
        state.no_progress_streak = 0
    else:
        state.no_progress_streak += 1
    if state.world_all_complete(contract) and state.first_completion_tokens is None:
        state.first_completion_tokens = state.tokens
    return (direct_progress, process_progress, in_scope)

def _policy_config(policy: str, token_budget: int) -> ControllerConfig:
    if policy == 'gec':
        return ControllerConfig(token_budget=token_budget)
    if policy == 'gec_no_scope':
        return ControllerConfig(token_budget=token_budget, enable_scope_gate=False)
    if policy == 'gec_no_value':
        return ControllerConfig(token_budget=token_budget, enable_value_gate=False)
    if policy == 'gec_no_progress':
        return ControllerConfig(token_budget=token_budget, enable_progress_breaker=False)
    return ControllerConfig(token_budget=token_budget)

def run_episode(scenario: Scenario, policy: str, seed: int, *, token_budget: int=40000, max_cycles: int=40, planning_tokens: int=120, candidate_batch_size: int=3, baseline_stop_probability: float=0.12, optional_probability: float=0.28, scope_false_negative_rate: float=0.0, scope_false_positive_rate: float=0.0, verifier_false_positive_rate: float=0.0, verifier_false_negative_rate: float=0.0, evidence_invalidation_rate: float=0.05, include_soft: bool=False, soft_probability: float=0.0) -> tuple[EpisodeMetrics, dict]:
    """Run one matched-candidate-set synthetic episode.

    Baseline, budget-only, and GEC see the same exogenous candidate sets and
    outcome draws. Baseline selects the first candidate, budget-only selects the
    cheapest feasible candidate, and GEC selects the highest-net-value governed
    candidate. No policy is allowed to alter the future proposal distribution.
    """
    allowed = {'baseline', 'budget_only', 'gec', 'gec_no_scope', 'gec_no_value', 'gec_no_progress'}
    if policy not in allowed:
        raise ValueError(f'Unknown policy: {policy}')
    contract = scenario.contract(include_soft=include_soft)
    state = TaskState()
    controller = GlobalExecutiveController(contract, _policy_config(policy, token_budget))
    batches = make_candidate_sets(scenario, seed, max_cycles=max_cycles, batch_size=candidate_batch_size, optional_probability=optional_probability, soft_probability=soft_probability if include_soft else 0.0)
    trace: list[dict] = []
    governed = policy.startswith('gec')
    for cycle, batch in enumerate(batches):
        if state.tokens >= token_budget:
            state.stop_reason = 'budget'
            break
        if governed:
            pre = controller.preflight(state)
            trace.append({'cycle': cycle, 'phase': 'preflight', 'decision': pre.decision.value})
            if pre.decision in {DecisionType.STOP_SUCCESS, DecisionType.STOP_BUDGET, DecisionType.STOP_BLOCKED}:
                state.stop_reason = pre.decision.value
                break
            if pre.decision == DecisionType.REPLAN:
                if state.tokens + planning_tokens >= token_budget:
                    state.stop_reason = 'budget'
                    break
                state.tokens += planning_tokens
                state.no_progress_streak = 0
                trace.append({'cycle': cycle, 'phase': 'replan', 'tokens': planning_tokens})
        elif state.all_complete(contract) and batch[0].stop_draw < baseline_stop_probability:
            state.stop_reason = 'probabilistic_success_stop'
            break
        if state.tokens + planning_tokens >= token_budget:
            state.stop_reason = 'budget'
            break
        state.tokens += planning_tokens
        trace.append({'cycle': cycle, 'phase': 'candidate_set', 'actions': [{'action_id': e.proposal.action_id, 'kind': e.proposal.kind.value, 'token_cost': e.proposal.token_cost, 'declared_links': [(l.target_id, l.link_type.value) for l in e.proposal.declared_links]} for e in batch]})
        chosen_event: CandidateEvent | None = None
        chosen_assessment: ScopeAssessment | None = None
        if governed:
            decisions: list[Decision] = []
            assessments: list[ScopeAssessment] = []
            for event in batch:
                proposal = event.proposal
                if policy == 'gec_no_scope':
                    assessment = ScopeAssessment(proposal.declared_links, source='generator_self_report', non_goal_match=False)
                else:
                    assessment = noisy_scope_assessment(event, contract, false_negative_rate=scope_false_negative_rate, false_positive_rate=scope_false_positive_rate)
                proposal_for_gate = proposal
                if policy == 'gec_no_scope' and proposal.kind == ActionKind.OPTIONAL and proposal.declared_links:
                    proposal_for_gate = replace(proposal, success_probability=0.7)
                decision = controller.evaluate_action(state, proposal_for_gate, assessment)
                decisions.append(decision)
                assessments.append(assessment)
            approved = [(idx, d) for idx, d in enumerate(decisions) if d.decision == DecisionType.APPROVE]
            state.rejected_actions += sum((1 for d in decisions if d.decision == DecisionType.REJECT))
            if approved:
                idx, best_decision = max(approved, key=lambda item: item[1].net_value if item[1].net_value is not None else float('-inf'))
                chosen_event = batch[idx]
                chosen_assessment = assessments[idx]
                trace.append({'cycle': cycle, 'phase': 'gate', 'chosen': chosen_event.proposal.action_id, 'net_value': best_decision.net_value})
            else:
                terminal = controller.classify_after_candidate_set(state, decisions, feasible_hard_path_exists=True)
                if terminal.decision in {DecisionType.STOP_ECONOMIC, DecisionType.STOP_BLOCKED, DecisionType.STOP_BUDGET, DecisionType.STOP_SUCCESS}:
                    state.stop_reason = terminal.decision.value
                    break
                state.no_progress_streak += 1
                trace.append({'cycle': cycle, 'phase': 'gate', 'chosen': None, 'decision': 'all_rejected'})
                continue
        elif policy == 'budget_only':
            feasible = [e for e in batch if state.tokens + e.proposal.token_cost <= token_budget]
            if not feasible:
                state.stop_reason = 'budget'
                break
            chosen_event = feasible[0]
            chosen_assessment = chosen_event.true_assessment
        else:
            chosen_event = batch[0]
            chosen_assessment = chosen_event.true_assessment
            if state.tokens + chosen_event.proposal.token_cost > token_budget:
                state.stop_reason = 'budget'
                break
        assert chosen_event is not None and chosen_assessment is not None
        _execute_event(state, chosen_event, scenario, contract, chosen_assessment, planning_tokens=planning_tokens, verifier_false_positive_rate=verifier_false_positive_rate, verifier_false_negative_rate=verifier_false_negative_rate, evidence_invalidation_rate=evidence_invalidation_rate)
        trace.append({'cycle': cycle, 'phase': 'state', 'chosen': chosen_event.proposal.action_id, 'world_completion': state.world_completion_fraction(contract), 'controller_completion': state.completion_fraction(contract), 'tokens': state.tokens, 'no_progress_streak': state.no_progress_streak})
    else:
        state.stop_reason = 'max_cycles'
    metrics = compute_metrics(state, contract, scenario.required_complexity)
    episode = {'scenario': scenario.name, 'policy': policy, 'seed': seed, 'stop_reason': state.stop_reason, 'metrics': metrics.as_dict(), 'trace': trace}
    return (metrics, episode)

def _mean_ci(values: Iterable[float]) -> tuple[float, float]:
    vals = [v for v in values if not math.isnan(v)]
    if not vals:
        return (float('nan'), float('nan'))
    mean = statistics.fmean(vals)
    if len(vals) < 2:
        return (mean, 0.0)
    se = statistics.stdev(vals) / math.sqrt(len(vals))
    return (mean, 1.96 * se)

def _summarize(metrics_list: list[EpisodeMetrics]) -> dict:
    out: dict[str, float] = {}
    for field in EpisodeMetrics.__dataclass_fields__.keys():
        vals = [float(getattr(m, field)) for m in metrics_list]
        mean, ci = _mean_ci(vals)
        out[field] = mean
        out[f'{field}_ci95'] = ci
    return out

def run_benchmark(output_dir: str | Path, *, episodes_per_scenario: int=2000, seed: int=20260911) -> list[dict]:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    policies = ('baseline', 'budget_only', 'gec')
    rows: list[dict] = []
    all_policy_metrics: dict[str, list[EpisodeMetrics]] = {p: [] for p in policies}
    trace_examples: list[dict] = []
    for s_idx, scenario in enumerate(SCENARIOS):
        for policy in policies:
            episode_metrics: list[EpisodeMetrics] = []
            for i in range(episodes_per_scenario):
                episode_seed = seed + s_idx * 100000 + i
                metrics, episode = run_episode(scenario, policy, episode_seed)
                episode_metrics.append(metrics)
                all_policy_metrics[policy].append(metrics)
                if i == 0:
                    trace_examples.append(episode)
            row = {'scenario': scenario.name, 'policy': policy, 'n': episodes_per_scenario}
            row.update(_summarize(episode_metrics))
            rows.append(row)
    with (output_dir / 'results_summary.csv').open('w', newline='', encoding='utf-8') as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    aggregate: list[dict] = []
    for policy in policies:
        out = {'policy': policy, 'scenarios': len(SCENARIOS), 'episodes': len(all_policy_metrics[policy])}
        out.update(_summarize(all_policy_metrics[policy]))
        aggregate.append(out)
    with (output_dir / 'aggregate_results.json').open('w', encoding='utf-8') as fh:
        json.dump(aggregate, fh, indent=2)
    with (output_dir / 'aggregate_results.csv').open('w', newline='', encoding='utf-8') as fh:
        writer = csv.DictWriter(fh, fieldnames=list(aggregate[0].keys()))
        writer.writeheader()
        writer.writerows(aggregate)
    with (output_dir / 'example_trajectories.json').open('w', encoding='utf-8') as fh:
        json.dump(trace_examples, fh, indent=2)
    return aggregate

def run_budget_sensitivity(output_csv: str | Path, *, budgets: tuple[int, ...]=(3000, 4000, 5000, 6000, 8000, 12000, 20000, 40000), episodes_per_scenario: int=500, seed: int=20260911) -> list[dict]:
    rows: list[dict] = []
    for budget in budgets:
        for policy in ('budget_only', 'gec'):
            vals: list[EpisodeMetrics] = []
            for s_idx, scenario in enumerate(SCENARIOS):
                for i in range(episodes_per_scenario):
                    episode_seed = seed + s_idx * 100000 + i
                    m, _ = run_episode(scenario, policy, episode_seed, token_budget=budget)
                    vals.append(m)
            row = {'budget': budget, 'policy': policy, 'n': len(vals)}
            row.update(_summarize(vals))
            rows.append(row)
    output_csv = Path(output_csv)
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    with output_csv.open('w', newline='', encoding='utf-8') as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    return rows

def run_ablation(output_csv: str | Path, *, episodes_per_scenario: int=500, seed: int=20260911) -> list[dict]:
    policies = ('gec', 'gec_no_scope', 'gec_no_value', 'gec_no_progress')
    rows: list[dict] = []
    for policy in policies:
        vals: list[EpisodeMetrics] = []
        for s_idx, scenario in enumerate(SCENARIOS):
            for i in range(episodes_per_scenario):
                episode_seed = seed + s_idx * 100000 + i
                m, _ = run_episode(scenario, policy, episode_seed)
                vals.append(m)
        row = {'policy': policy, 'n': len(vals)}
        row.update(_summarize(vals))
        rows.append(row)
    output_csv = Path(output_csv)
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    with output_csv.open('w', newline='', encoding='utf-8') as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    return rows

def run_noise_robustness(output_csv: str | Path, *, noise_levels: tuple[float, ...]=(0.0, 0.02, 0.05, 0.1), episodes_per_scenario: int=300, seed: int=20260911) -> list[dict]:
    rows: list[dict] = []
    for q in noise_levels:
        vals: list[EpisodeMetrics] = []
        for s_idx, scenario in enumerate(SCENARIOS):
            for i in range(episodes_per_scenario):
                episode_seed = seed + s_idx * 100000 + i
                m, _ = run_episode(scenario, 'gec', episode_seed, scope_false_negative_rate=q, scope_false_positive_rate=q, verifier_false_positive_rate=q / 2, verifier_false_negative_rate=q)
                vals.append(m)
        row = {'noise_level': q, 'n': len(vals)}
        row.update(_summarize(vals))
        rows.append(row)
    output_csv = Path(output_csv)
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    with output_csv.open('w', newline='', encoding='utf-8') as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    return rows

def run_soft_value_probe(seed: int=1234) -> dict:
    """Deterministic demonstration that GEC can accept beneficial soft work after hard completion.

    Economic stopping is assessed over a candidate *set*, never from one bad candidate.
    """
    scenario = SCENARIOS[0]
    contract = scenario.contract(include_soft=True)
    state = TaskState()
    for cid in contract.hard_ids():
        state.world_satisfied.add(cid)
        state.evidence[cid] = Evidence(cid, True, 'external', confidence=0.99)
    controller = GlobalExecutiveController(contract)
    good = ActionProposal('soft-good', 'Create low-cost governed diagnostic summary', ActionKind.SOFT, token_cost=200, complexity_delta=0.0, risk=0.0, success_probability=0.95)
    bad = ActionProposal('soft-bad', 'Create expensive optional dashboard redesign', ActionKind.SOFT, token_cost=8000, complexity_delta=1.0, risk=0.2, success_probability=0.2)
    assessment = ScopeAssessment((ScopeLink('S1', LinkType.SOFT, 0.99),))
    decisions = [controller.evaluate_action(state, p, assessment) for p in (good, bad)]
    terminal = controller.classify_after_candidate_set(state, decisions)
    return {'good': decisions[0].decision.value, 'good_net': decisions[0].net_value, 'bad': decisions[1].decision.value, 'bad_net': decisions[1].net_value, 'terminal': terminal.decision.value}
