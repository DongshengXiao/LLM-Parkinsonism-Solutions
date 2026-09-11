# Experimental Results

## Main controlled synthetic benchmark

Configuration: 6 scenarios x 3 policies x 2,000 episodes = **36,000 episodes**. Same stochastic proposal generator in all conditions. Seed root: `20260911`.

| Metric | Baseline | Budget only | GEC |
|---|---:|---:|---:|
| Success | 1.000 | 1.000 | 1.000 |
| Mean total tokens | 13,039.96 | 13,013.36 | **4,120.64** |
| Useful Token Ratio | 0.3761 | 0.3721 | **0.8960** |
| Token Efficiency (verified utility/1k tokens) | 0.1063 | 0.1051 | **0.2552** |
| Nonproductive Persistence Ratio | 0.6239 | 0.6279 | **0.1040** |
| Termination Overrun Ratio | 0.4326 | 0.4355 | **0.0000** |
| Goal Drift Rate | 0.6228 | 0.6274 | **0.0000** |
| Complexity Accretion Index | 0.9792 | 0.9802 | **0.0556** |
| LLM Parkinsonism Index | 57.73 | 58.16 | **4.48** |
| Executed actions | 12.95 | 12.94 | **3.52** |

Relative to baseline, GEC:

- reduced mean total tokens by **68.4%**;
- increased Token Efficiency by **2.40x**;
- reduced executed actions by **72.8%**;
- reduced LPI by **92.2%**;
- eliminated post-completion token overrun in the benchmark by design because verified completion is a terminal preflight state.

The budget-only condition is intentionally informative: with a generous 40k-token ceiling, it behaves almost identically to the local-loop baseline. A ceiling limits worst-case exposure but does not itself solve goal drift, complexity accretion, or completion recognition.

## Budget sensitivity

Each row: 6 scenarios x 500 episodes = 3,000 episodes per policy/budget.

| Budget | Budget-only success | GEC success | Budget-only TE | GEC TE |
|---:|---:|---:|---:|---:|
| 3,000 | 4.33% | **8.27%** | 0.1707 | **0.2375** |
| 4,000 | 21.93% | **50.47%** | 0.1654 | **0.2457** |
| 5,000 | 42.27% | **84.00%** | 0.1623 | **0.2525** |
| 6,000 | 59.07% | **95.10%** | 0.1530 | **0.2544** |
| 8,000 | 81.57% | **99.70%** | 0.1376 | **0.2556** |
| 12,000 | 97.57% | **100%** | 0.1173 | **0.2551** |
| 20,000 | 100% | **100%** | 0.1078 | **0.2545** |
| 40,000 | 100% | **100%** | 0.1061 | **0.2557** |

Interpretation: under tight budgets, GEC spends a greater fraction of the budget on criterion-closing work and therefore reaches the verified goal more often. Under loose budgets, both can succeed, but the uncontrolled agent keeps spending on low-value tail work.

## Limitations

These are controlled **synthetic** experiments. The benchmark is designed to isolate executive-control mechanisms and therefore should not be read as an estimate of the prevalence or magnitude of the phenomenon in any named commercial model. Live-model validation is specified separately in `docs/LIVE_EVALUATION_PROTOCOL.md`.
