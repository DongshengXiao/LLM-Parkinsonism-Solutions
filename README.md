# LLM Parkinsonism Solutions

Research prototype accompanying the manuscript **"LLM Parkinsonism: Executive-Control Failure, Token-Inefficient Persistence, and a Global Executive Control Architecture for Autonomous Language-Model Agents."**

> **Important terminology note:** “LLM Parkinsonism” is a computational-behavior metaphor, not a medical diagnosis and not a claim of mechanistic equivalence between Parkinson disease and language models. The analogy is limited to a surface pattern: large early task steps followed by progressively smaller actions, continued activity after diminishing utility, and unreliable project-level stopping.

## Core idea

Modern LLM agents are excellent at proposing the *next* locally plausible action, but local next-action competence does not imply global executive control. Four measurable failure modes are studied here:

1. **Goal drift** — actions are no longer traceable to the original acceptance criteria.
2. **Complexity accretion** — optional abstractions create new dependencies and repair work.
3. **Termination failure** — the agent keeps acting after the original goal is already verified.
4. **Token-inefficient persistence** — a large fraction of tokens produces no verified increase in task utility.

The repository introduces a **Global Executive Controller (GEC)** that sits above an arbitrary planner/executor and enforces:

- an immutable **Goal Contract**;
- requirement-to-action linkage;
- externally grounded verification;
- a **complexity tax**;
- a marginal-value / token-cost gate;
- a no-progress circuit breaker;
- explicit `DONE`, `GOOD_ENOUGH`, and `BLOCKED` terminal semantics.

## Main benchmark result

Controlled synthetic benchmark, 6 task families, 2,000 episodes per scenario per policy (36,000 main episodes total). The proposal generator is held fixed; only governance differs.

| Policy | Success | Mean tokens | Useful-token ratio | Token efficiency (verified utility / 1k tokens) | Termination overrun | Goal drift | LLM Parkinsonism Index |
|---|---:|---:|---:|---:|---:|---:|---:|
| Baseline local loop | 100% | 13,039.96 | 37.61% | 0.1063 | 43.26% | 62.28% | 57.73 |
| Budget only | 100% | 13,013.36 | 37.21% | 0.1051 | 43.55% | 62.74% | 58.16 |
| **GEC** | **100%** | **4,120.64** | **89.60%** | **0.2552** | **0%** | **0%** | **4.48** |

Relative to the baseline, GEC reduces mean token consumption by **68.4%**, raises token efficiency by **2.40×**, and reduces the operational LLM Parkinsonism Index by **92.2%** in this controlled environment.

These numbers are **simulation results**, not measurements of a specific commercial LLM. The repository includes a prespecified live-model validation protocol for subsequent frontier-model experiments.

## Quick start

```bash
python -m pip install -e .
pytest -q
llm-parkinsonism benchmark --output experiments/results --episodes 2000
```

Reproduce the paper experiments:

```bash
PYTHONPATH=src python experiments/run_benchmark.py
PYTHONPATH=src python experiments/run_sensitivity.py
```

## Repository structure

```text
src/llm_parkinsonism/      Core GEC, state model, metrics, benchmark simulator
benchmarks/                Frozen LPB v0.1 task definitions
experiments/               Reproduction scripts and generated results
paper/                     Manuscript and references
docs/                      Architecture and live-evaluation protocol
tests/                     Unit tests
```

## New metrics

Let `U_verified` be normalized task utility certified by external evidence and `T` be consumed tokens.

- **Token Efficiency (TE)** = `1000 * U_verified / T`
- **Useful Token Ratio (UTR)** = tokens attributable to actions that close a frozen acceptance criterion / total tokens
- **Termination Overrun Ratio (TOR)** = tokens consumed after the first verified-complete state / total tokens
- **Goal Drift Rate (GDR)** = executed actions with no link to an unmet frozen criterion / all executed actions
- **Complexity Accretion Index (CAI)** = optional positive complexity added / required baseline complexity
- **LLM Parkinsonism Index (LPI)** = bounded composite of nonproductive persistence, termination overrun, goal drift, and complexity accretion

The paper treats LPI as an **operational benchmark score**, not a clinical measure. Token Efficiency is the primary economic metric.

## Watchdog motivating example

Frozen goal:

```text
A DOWN -> A NODE DOWN ALERT
B DOWN -> B NODE DOWN ALERT
A+B DOWN -> both node-level alerts remain observable
Recovery -> healthy state restored
```

Non-goals:

```text
SITE DOWN correlation
suppression of individual node alerts
cross-node inference
```

A proposal such as “add SITE DOWN correlation and suppress individual alerts” is rejected because it closes no unmet criterion and adds state/dependency complexity. The executor may *suggest* it, but cannot promote it into a hard requirement.

## Status

- Core architecture implemented.
- 9 unit tests passing.
- Main 36,000-episode controlled synthetic benchmark completed.
- 48,000-episode budget sensitivity study completed.
- Paper draft included.
- Live frontier-model evaluation is intentionally separated from the synthetic results and is not claimed as completed.
