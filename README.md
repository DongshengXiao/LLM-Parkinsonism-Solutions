# LLM Parkinsonism Solutions — GEC v0.2

Research code accompanying **“LLM Parkinsonism: Executive-Control Failure, Token-Inefficient Persistence, and an Uncertainty-Aware Global Executive Control Architecture for Autonomous Language-Model Agents.”**

> “LLM Parkinsonism” is a deliberately limited computational-behavior metaphor, not a diagnosis and not a claim of mechanistic homology with Parkinson disease.

## What changed in v0.2

GEC v0.2 addresses the principal validity problems identified in the first prototype:

- **Candidate-level low value no longer stops the project.** A low-value action is rejected; `STOP_ECONOMIC` is a state-level decision after hard requirements are complete and no candidate in the governed continuation set has positive value.
- **Hard requirements and soft objectives are separated.** `STOP_BLOCKED` / `STOP_BUDGET` cannot be mislabeled as success.
- **Scope linkage is causal, not only criterion-closing.** `DIRECT`, `PREREQUISITE`, `VERIFICATION`, `RISK_MITIGATION`, and `SOFT` links are supported.
- **The generator does not own scope authority.** The controller consumes an independent `ScopeAssessment`; generator self-declared links are non-authoritative.
- **Evidence is typed, confidence-bearing, state-versioned, and invalidatable.** Completion depends on valid external evidence rather than a Boolean flag.
- **Expected utility is contract-aligned.** Direct hard-goal value is derived from criterion weight and action success probability.
- **Goal Contract changes are governed events.** Anonymous/self-authorized amendments are rejected.
- **Progress includes validated prerequisites and new valid evidence**, not only binary criterion closure.
- **Pre-completion drift is separated from post-completion overrun.** Gross complexity is separated from residual net complexity.
- **LPB v0.2 uses matched exogenous candidate sets/common random numbers.** Policies face the same action opportunities; GEC can no longer improve merely by forcing the proposal generator to emit required work.

## Core decision rules

```text
low value of one candidate -> REJECT(candidate), not STOP_PROJECT

STOP_SUCCESS:
    all hard requirements have valid evidence

STOP_ECONOMIC:
    hard requirements complete
    AND no governed continuation candidate has positive net value

STOP_BLOCKED:
    hard requirements incomplete
    AND no feasible governed path remains
```

## LPB v0.2 main benchmark

Six task families, three policies, 1,000 episodes per scenario-policy cell: **18,000 episodes**. All policies use the same 40,000-token hard ceiling and matched candidate sets.

| Policy | Hard-goal success | Mean total tokens | Tokens to first completion* | TE | TOR | Pre-completion GDR | Gross CAI |
|---|---:|---:|---:|---:|---:|---:|---:|
| Baseline local loop | 67.42% | 32,058 | 23,719 | 0.0317 | 0.1249 | 0.2721 | 1.6543 |
| Budget-only | 67.85% | 32,170 | 23,819 | 0.0317 | 0.1256 | 0.2718 | 1.6604 |
| **GEC v0.2** | **96.57%** | **12,574** | **12,158** | **0.0963** | **0.0000** | **0.0000** | **0.1228** |

\*Conditional on trajectories that reached first completion.

Relative to baseline, GEC v0.2 improved success by **29.15 percentage points**, reduced mean total token use by **60.8%**, and reduced tokens to first completion by **48.7%** among completed trajectories. TE was 3.04× higher, but TE is treated as secondary because at equal final utility it is an inverse-cost transformation.

These are **synthetic mechanism-isolation results**, not estimates for any commercial model.

## Additional experiments

- **Budget sensitivity:** 14,400 episodes; normalized success-vs-log-budget AUC = **0.467 GEC vs 0.167 budget-only**.
- **Component ablation:** 7,200 episodes. Trusting generator scope self-report reintroduced pre-completion drift (GDR=0.0716) and increased gross complexity (CAI 0.3144 vs 0.1243). Removing the value gate increased mean tokens from 12,733 to 14,500.
- **No-progress breaker:** removing it slightly improved efficiency in LPB v0.2 because the exogenous proposal stream cannot be altered by replanning. The repository therefore does **not** claim synthetic evidence for this component’s independent benefit.
- **Noise robustness:** 3,600 episodes with synthetic scope/verifier noise up to 0.10; success remained about 96%.
- **Beneficial-soft-work probe:** a positive-value soft action is approved while an expensive low-yield soft action is rejected; one bad candidate does not cause project-level economic stopping.

## Quick start

```bash
python -m pip install -e .
pytest -q
llm-parkinsonism benchmark --output experiments/results --episodes 1000
```

Full reproduction:

```bash
PYTHONPATH=src python experiments/run_benchmark.py
PYTHONPATH=src python experiments/run_budget_sensitivity.py
PYTHONPATH=src python experiments/run_ablation.py
PYTHONPATH=src python experiments/run_noise_robustness.py
```

## Repository structure

```text
src/llm_parkinsonism/      GEC v0.2 controller, state/evidence model, metrics, LPB simulator
benchmarks/                LPB v0.1 (historical) and LPB v0.2 definitions
experiments/               Reproduction scripts and machine-readable results
paper/                     Revised manuscript and references
docs/                      Architecture and live-model validation protocol
tests/                     Unit tests
```

## Primary metrics

- **Hard-goal success** — externally evaluated completion of all hard criteria.
- **Tokens to first completion** — cost at the first externally complete hard-goal state.
- **Token Efficiency (TE)** = `1000 * externally evaluated hard utility / total tokens` (secondary economic summary).
- **Termination Overrun Ratio (TOR)** — post-completion token tail.
- **Pre-completion Goal Drift Rate (GDR_pre)** — unscoped executed actions before first completion / all pre-completion executed actions.
- **Gross Complexity Accretion Index** — cumulative positive complexity / required baseline complexity.
- **Net Complexity Index** — residual positive net complexity / required baseline complexity.
- **Executive Persistence Index (EPI)** — exploratory descriptive composite; not a clinical measure and not a primary endpoint.

## Status

- GEC v0.2 architecture implemented.
- 13 unit tests passing locally for the research revision.
- LPB v0.2 main, budget, ablation, and noise experiments completed.
- Revised manuscript included.
- Live frontier-model validation remains future work and is not claimed as completed.
