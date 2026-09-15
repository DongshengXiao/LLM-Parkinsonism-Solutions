# Global Executive Control v0.2 Architecture

## 1. Goal Contract

The governed objective is

`G = (g, R_H, R_S, N, C, M)`

where `R_H` are hard requirements, `R_S` are authorized soft objectives, `N` are explicit non-goals, `C` are constraints, and `M` is the contract-amendment policy.

The executor may propose a contract change, but it cannot authorize one. `ContractAmendment` requires an external authorizer and creates a new contract revision.

## 2. Candidate set, not single-proposal destiny

The planner emits a candidate set. GEC evaluates candidates separately and selects the highest-net-value approved action. A low-value candidate is rejected; it is not evidence that all possible continuation is low value.

## 3. Independent scope authority

The planner may provide `declared_links`, but the controller consumes a separate `ScopeAssessment`:

- `DIRECT`
- `PREREQUISITE`
- `VERIFICATION`
- `RISK_MITIGATION`
- `SOFT`
- `NONE`
- `FORBIDDEN`

This closes the circular loophole in which a generator could label its own optional proposal as “required.”

## 4. Contract-aligned expected utility

For a direct hard-goal action targeting criterion `r_i`:

`E[ΔU_H] = p_success(a) * w_i / Σ_j w_j`

Prerequisite and risk-mitigation links receive discounted enabling value. Soft utility is separately weighted and cannot silently become hard utility.

The action score is:

`V(a|s) = E[ΔU] - λ_T C_T - λ_K C_K - λ_R C_R - λ_V C_V`

If `V(a|s) <= τ`, the action is rejected. `STOP_ECONOMIC` is decided only at state level after hard completion and candidate-set evaluation.

## 5. Evidence-carrying completion

`Evidence` records criterion ID, pass/fail status, source, state version, confidence, dependencies, and validity. A criterion is complete only when usable evidence exists. Later actions can invalidate evidence.

This prevents stale “passed once” evidence from acting as a permanent completion certificate after the system changes.

## 6. Process progress

The circuit breaker tracks more than hard-criterion closure. Progress includes:

- hard-goal utility increase;
- validated prerequisite completion;
- newly valid verification evidence;
- independently grounded risk/process progress.

The current LPB v0.2 ablation does not show an independent benefit for the no-progress breaker because replanning cannot alter the matched exogenous candidate stream. This is intentionally documented rather than hidden.

## 7. Terminal states

- `STOP_SUCCESS`: all hard requirements carry valid evidence (and all soft objectives if the caller requests full completion).
- `STOP_ECONOMIC`: hard requirements are complete and no governed continuation candidate has positive net value.
- `STOP_BLOCKED`: hard requirements remain incomplete and no feasible governed path exists.
- `STOP_BUDGET`: budget exhausted before governed completion.

## 8. Complexity accounting

GEC reports both cumulative positive complexity (`K_gross+`) and residual net complexity (`K_net`). Gross accounting prevents add-then-delete thrashing from disappearing behind a net-zero final state.

The deletion-first preference (`DELETE -> SIMPLIFY -> FIX -> ADD`) remains a design principle; LPB v0.2 does not yet contain a dedicated complexity-reversal benchmark.

## 9. LPB v0.2 causal-comparison design

Each episode pre-generates matched candidate sets and random execution draws. All policies see the same opportunity stream. No policy may call `force_required` or otherwise change the future proposal distribution.

- Baseline selects the first candidate.
- Budget-only preserves proposal order but skips candidates that cannot fit the remaining hard budget.
- GEC independently adjudicates each candidate and selects the approved candidate with highest net value.

This design isolates governance more cleanly than LPB v0.1.
