from __future__ import annotations

import argparse
import json
from pathlib import Path

from .simulation import run_ablation, run_benchmark, run_budget_sensitivity, run_noise_robustness, run_soft_value_probe


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="GEC v0.2 and LPB v0.2 research prototype")
    sub = parser.add_subparsers(dest="command", required=True)

    bench = sub.add_parser("benchmark", help="run the matched-candidate main benchmark")
    bench.add_argument("--output", default="experiments/results")
    bench.add_argument("--episodes", type=int, default=1000, help="episodes per scenario per policy")
    bench.add_argument("--seed", type=int, default=20260911)

    sub.add_parser("budget", help="run budget sensitivity")
    sub.add_parser("ablation", help="run component ablations")
    sub.add_parser("noise", help="run scope/verifier noise robustness")
    sub.add_parser("soft-probe", help="run beneficial-soft-work decision probe")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.command == "benchmark":
        result = run_benchmark(Path(args.output), episodes_per_scenario=args.episodes, seed=args.seed)
    elif args.command == "budget":
        result = run_budget_sensitivity("experiments/results/budget_sensitivity.csv", episodes_per_scenario=150)
    elif args.command == "ablation":
        result = run_ablation("experiments/results/ablation.csv", episodes_per_scenario=300)
    elif args.command == "noise":
        result = run_noise_robustness("experiments/results/noise_robustness.csv", episodes_per_scenario=150)
    else:
        result = run_soft_value_probe()
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
