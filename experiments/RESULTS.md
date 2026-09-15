# LPB v0.2 Synthetic Results

All results below are mechanistic simulations under fixed synthetic scenarios and parameters. They are not measurements of a named commercial LLM.

## Main matched-candidate benchmark — 18,000 episodes

| Policy | Success | Mean tokens | Tokens to first completion* | TE | TOR | GDR_pre | Gross CAI |
|---|---:|---:|---:|---:|---:|---:|---:|
| Baseline | 0.6742 | 32,058 | 23,719 | 0.0317 | 0.1249 | 0.2721 | 1.6543 |
| Budget-only | 0.6785 | 32,170 | 23,819 | 0.0317 | 0.1256 | 0.2718 | 1.6604 |
| GEC v0.2 | **0.9657** | **12,574** | **12,158** | **0.0963** | **0** | **0** | **0.1228** |

\*Conditional on completion.

GEC vs baseline: +29.15 percentage points success, -60.8% total tokens, -48.7% tokens to first completion, 3.04× TE.

Zero TOR and zero pre-completion GDR under default GEC are partly enforcement properties; the more informative outcomes are success and cost under matched candidate opportunities.

## Budget sensitivity — 14,400 episodes

Normalized success-vs-log-budget AUC:

- budget-only: **0.167**
- GEC: **0.467**

At 40k: budget-only success 68.67%; GEC 96.33%.

## Ablation — 7,200 episodes

| Policy | Success | Mean tokens | TE | GDR_pre | Gross CAI |
|---|---:|---:|---:|---:|---:|
| Full GEC | 0.9611 | 12,733 | 0.0951 | 0 | 0.1243 |
| No independent scope authority | 0.9522 | 14,036 | 0.0874 | 0.0716 | 0.3144 |
| No value gate | 0.9600 | 14,500 | 0.0862 | 0 | 0.1263 |
| No progress breaker | 0.9611 | 12,318 | 0.0977 | 0 | 0.1243 |

The no-progress breaker does not show a positive independent effect in LPB v0.2 because replanning cannot alter the exogenous candidate stream. This negative result is retained explicitly.

## Noise robustness — 3,600 episodes

GEC hard-goal success remained approximately 96% across nominal injected scope/verifier noise levels from 0 to 0.10. This is a synthetic random-noise stress test, not real-world error calibration.

## Beneficial-soft probe

- low-cost governed soft action: **APPROVE**, net value 0.2321
- expensive low-yield soft action: **REJECT**, net value -0.1605
- candidate-set terminal decision: **CONTINUE**

This confirms that one bad candidate is not promoted into a project-level economic stop.
