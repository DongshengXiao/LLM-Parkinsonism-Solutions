# Global Executive Control (GEC) Architecture

## 1. Design principle

The proposal-generating model should not simultaneously own the authority to redefine the goal, certify its own success, and decide indefinitely whether to continue. GEC separates **generation** from **executive control**.

```text
Frozen Goal Contract
        |
        v
Planner / LLM proposal generator
        |
        v
+-------------------------------+
| Global Executive Controller   |
|                               |
| 1. Scope / requirement gate   |
| 2. Evidence ledger            |
| 3. Marginal-value gate        |
| 4. Complexity tax             |
| 5. Token-budget gate          |
| 6. No-progress breaker        |
| 7. Terminal-state classifier  |
+-------------------------------+
        |
  APPROVE / REJECT / REPLAN / STOP
        |
        v
Executor -> External Verifier -> Evidence Ledger
        ^                         |
        +-------------------------+
```

## 2. Frozen Goal Contract

A Goal Contract contains:

- a primary goal;
- finite acceptance criteria;
- criterion weights;
- explicit non-goals.

The executor may generate suggestions but cannot silently mutate the contract. Formally:

```text
LLM proposal != project requirement
```

A change to the Goal Contract is an external governance event, not an ordinary agent action.

## 3. Requirement linkage

Every candidate action must answer:

```text
Which currently unmet original acceptance criterion does this action close?
```

If the answer is `None`, the action is optional. Under the default controller, optional actions are rejected during the completion-critical loop.

## 4. External verification

Success is represented by criterion-linked evidence, not by the executor's self-report. In production, evidence can be produced by deterministic tests, health endpoints, database assertions, checksums, UI state, or independent verifier agents.

## 5. Marginal-value gate

For action `a` at state `s`:

```text
NetValue(a|s) = ExpectedUtility(a|s)
                - TokenPenalty(a)
                - ComplexityTax(a)
                - RiskPenalty(a)
```

Only actions with positive expected net value and valid scope linkage are approved.

## 6. Complexity tax and delete-first policy

Positive complexity deltas are penalized. The intended production policy is:

```text
DELETE? -> SIMPLIFY? -> FIX -> ADD
```

rather than the common agentic pattern:

```text
FIX -> ADD ABSTRACTION -> ADD TEST -> REPAIR ABSTRACTION -> ADD MONITOR
```

## 7. Three stop modes

GEC distinguishes:

- `STOP_SUCCESS` / **DONE**: all frozen criteria are externally verified.
- `STOP_ECONOMIC` / **GOOD_ENOUGH**: marginal expected utility is below marginal cost.
- `STOP_BLOCKED` / **BLOCKED**: required work cannot be completed within the declared constraints.

This avoids conflating “not worth continuing” with “success.”

## 8. No-progress circuit breaker

After `k` consecutive cycles with no increase in externally verified goal utility, local repair is suspended. The controller requires global replanning rather than another nearly identical retry.

Default in the prototype: `k = 3`.

## 9. Why a deterministic controller?

The prototype deliberately makes the executive gate deterministic. An LLM-based controller can reproduce the same biases as the executor and also consumes additional tokens. Deterministic scope, budget, and evidence checks make stopping auditable. LLM judgment can still be used upstream to estimate expected utility or downstream for ambiguous verification, but it is not the only authority at the terminal boundary.
