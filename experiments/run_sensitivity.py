"""Reproduce budget-sensitivity experiments for the paper."""

from __future__ import annotations

import csv
import statistics
from pathlib import Path

from llm_parkinsonism.simulation import SCENARIOS, run_episode


BUDGETS = (3000, 4000, 5000, 6000, 8000, 12000, 20000, 40000)
POLICIES = ("budget_only", "gec")
EPISODES_PER_SCENARIO = 500
SEED = 20260911


def main() -> None:
    out = Path("experiments/results/budget_sensitivity.csv")
    out.parent.mkdir(parents=True, exist_ok=True)
    rows = []

    for budget in BUDGETS:
        for policy in POLICIES:
            metrics = []
            for s_idx, scenario in enumerate(SCENARIOS):
                for i in range(EPISODES_PER_SCENARIO):
                    seed = SEED + budget * 1000 + s_idx * 10_000 + i + (0 if policy == "budget_only" else 1_000_000)
                    m, _ = run_episode(scenario, policy, seed=seed, token_budget=budget)
                    metrics.append(m)
            rows.append(
                {
                    "budget": budget,
                    "policy": policy,
                    "episodes": len(metrics),
                    "success_rate": statistics.fmean(m.success for m in metrics),
                    "mean_tokens": statistics.fmean(m.total_tokens for m in metrics),
                    "token_efficiency": statistics.fmean(m.token_efficiency for m in metrics),
                    "useful_token_ratio": statistics.fmean(m.useful_token_ratio for m in metrics),
                    "llm_parkinsonism_index": statistics.fmean(m.llm_parkinsonism_index for m in metrics),
                }
            )

    with out.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    for row in rows:
        print(row)


if __name__ == "__main__":
    main()
