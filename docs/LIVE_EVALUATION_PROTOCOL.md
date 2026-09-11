# Prespecified Live-Model Evaluation Protocol

This protocol is included to prevent the controlled synthetic results from being misrepresented as frontier-model measurements.

## Objective

Test whether real tool-using LLM agents exhibit the four operational features of LLM Parkinsonism and whether GEC improves Token Efficiency without materially reducing task success.

## Models

Run at least three model families, including one frontier reasoning model and one lower-cost model. Record exact model IDs, dates, reasoning-effort settings, and provider API versions.

## Conditions

For each frozen task and random seed / environment instance:

1. **Local-loop baseline** — standard planner/executor; after each successful step, the orchestration asks for the next action until the model emits a terminal action or the hard safety cap fires.
2. **Budget-only** — same baseline plus the same hard token budget used by GEC.
3. **GEC** — same proposal model and tools, wrapped by the deterministic Global Executive Controller.

Do not change the base model, temperature, tool surface, or acceptance criteria between conditions.

## Tasks

Use LPB v0.1 plus at least two real software tasks with deterministic tests. For the watchdog task, keep the non-goals explicit and do not reward SITE-level aggregation.

## Minimum sample

- 30 independent trials per task x model x condition for pilot inference.
- Prefer 100+ trials per cell for stable tail metrics.

## Required logging

For every model/tool call record:

- input tokens;
- output/reasoning tokens when exposed;
- tool-call count;
- wall time;
- action proposal;
- linked acceptance criterion (or `None`);
- pre/post externally verified utility;
- complexity delta annotation;
- time/token index at first verified complete state;
- final stop reason.

## Primary endpoint

**Token Efficiency (TE)**:

```text
TE = 1000 * externally_verified_task_utility / total_tokens
```

## Secondary endpoints

- Task success rate
- Useful Token Ratio
- Termination Overrun Ratio
- Goal Drift Rate
- Complexity Accretion Index
- LLM Parkinsonism Index
- Tool calls and wall time

## Key hypothesis tests

H1. Baseline agents consume non-zero post-completion tail tokens more often than GEC.

H2. GEC increases Token Efficiency while maintaining non-inferior task success.

H3. A hard budget alone is less effective than goal/evidence/complexity-aware executive control at equal budgets.

H4. The probability of unscoped actions increases as the number of unmet acceptance criteria approaches zero in baseline agents.

## Statistical analysis

- Report means, medians, 95% bootstrap confidence intervals, and heavy-tail percentiles (P90/P95) for token cost.
- Compare success with paired or stratified non-inferiority analysis where task instances are matched.
- Compare token metrics with paired bootstrap or permutation tests.
- Predefine a non-inferiority margin for success before observing live results.
- Publish complete trajectories after removing secrets and private data.

## Safety cap

All conditions must retain an independent hard maximum on token use, tool calls, and wall time. GEC is an efficiency/control mechanism, not a replacement for runtime safety limits.
