# Prespecified Live-Model Evaluation Protocol for GEC v0.2

## Objective

Test whether project-level executive governance improves resource efficiency without degrading externally adjudicated hard-goal success in real tool-using LLMs.

## Conditions

For each paired task instance use the same:

- base model and model version;
- temperature / reasoning-effort setting;
- tool surface and permissions;
- initial environment state;
- Goal Contract and acceptance criteria;
- context available at trial start.

Compare baseline local-loop, budget-only, and GEC governance. Share common randomness and exogenous environment events where technically possible.

## Primary endpoints

1. **Externally adjudicated hard-goal success.** Prespecify superiority or non-inferiority hypotheses.
2. **Tokens to first verified hard-goal completion** among paired successful trials.

Do not use TE as the sole primary endpoint; at equal final utility it is an inverse-cost transformation.

## Secondary endpoints

- Token Efficiency (TE)
- Termination Overrun Ratio (TOR)
- Pre-completion Goal Drift Rate (GDR_pre)
- Gross and net complexity
- tool calls
- wall time
- P50/P90/P95 token cost
- contract-amendment frequency
- evidence invalidation / re-verification events
- blocked/budget/economic terminal-state frequency
- scope-adjudication disagreement rate

## Scope adjudication

The proposing model must not be the only authority for whether its action is in scope. Use deterministic dependency rules where possible; otherwise use a separate blinded model, human evaluator, or ensemble. Audit a sample of scope-link decisions with double coding.

Allowed link classes:

`DIRECT`, `PREREQUISITE`, `VERIFICATION`, `RISK_MITIGATION`, `SOFT`, `NONE`, `FORBIDDEN`.

## Evidence

Prefer deterministic tests and observable environment assertions over LLM judges. Record verifier identity, timestamp/state version, confidence, dependencies, and invalidation events. If later changes touch dependencies, require re-verification.

## Task set requirements

Include tasks with:

- multi-step prerequisite chains;
- legitimately beneficial optional/soft improvements;
- explicit non-goals;
- changing goals that require authorized contract amendments;
- later changes that invalidate earlier evidence;
- blocked tasks where escalation is correct;
- tasks with multiple plausible candidate actions of different costs.

## Statistical analysis

Use paired bootstrap or permutation inference for token/cost outcomes. Report exact input/output tokens and provider-billed totals; report separate reasoning tokens when exposed by the provider. Report heavy-tail percentiles because runaway trajectories may be skewed.

For budget sensitivity, report success across several token ceilings and normalized AUC over log budget.

## Interpretation rule

Synthetic LPB results establish mechanism behavior, not real-model prevalence or effect size. The live study must be reported separately and must not back-fill commercial-model claims into the synthetic benchmark.
