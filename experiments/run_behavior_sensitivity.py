"""Sensitivity to local-agent stopping propensity and optional-action propensity."""

from __future__ import annotations

import csv
import statistics
from pathlib import Path

from llm_parkinsonism.simulation import SCENARIOS, run_episode


STOP_PROBS = (0.05, 0.12, 0.25, 0.50)
OPTIONAL_PROBS = (0.10, 0.28, 0.50)
EPISODES_PER_SCENARIO = 300
SEED = 20260911


def collect(policy: str, stop_p: float, optional_p: float):
    metrics = []
    for s_idx, scenario in enumerate(SCENARIOS):
        for i in range(EPISODES_PER_SCENARIO):
            seed = SEED + int(stop_p*1000)*100000 + int(optional_p*1000)*1000 + s_idx*10000 + i + (1_000_000 if policy == 'gec' else 0)
            m, _ = run_episode(
                scenario,
                policy,
                seed=seed,
                baseline_stop_probability=stop_p,
                optional_probability=optional_p,
            )
            metrics.append(m)
    return metrics


def main():
    out = Path('experiments/results/behavior_sensitivity.csv')
    rows=[]
    for stop_p in STOP_PROBS:
        for optional_p in OPTIONAL_PROBS:
            for policy in ('baseline','gec'):
                m=collect(policy,stop_p,optional_p)
                rows.append({
                    'baseline_stop_probability': stop_p,
                    'optional_probability': optional_p,
                    'policy': policy,
                    'episodes': len(m),
                    'success_rate': statistics.fmean(x.success for x in m),
                    'mean_tokens': statistics.fmean(x.total_tokens for x in m),
                    'token_efficiency': statistics.fmean(x.token_efficiency for x in m),
                    'termination_overrun_ratio': statistics.fmean(x.termination_overrun_ratio for x in m),
                    'goal_drift_rate': statistics.fmean(x.goal_drift_rate for x in m),
                    'lpi': statistics.fmean(x.llm_parkinsonism_index for x in m),
                })
    with out.open('w',newline='',encoding='utf-8') as fh:
        writer=csv.DictWriter(fh,fieldnames=list(rows[0].keys()))
        writer.writeheader(); writer.writerows(rows)
    print(out)

if __name__=='__main__':
    main()
