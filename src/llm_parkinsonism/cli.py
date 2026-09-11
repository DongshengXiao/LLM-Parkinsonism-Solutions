from __future__ import annotations

import argparse
import json
from pathlib import Path

from .simulation import run_benchmark


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="LLM Parkinsonism benchmark and Global Executive Control prototype")
    sub = parser.add_subparsers(dest="command", required=True)

    bench = sub.add_parser("benchmark", help="run the synthetic controlled benchmark")
    bench.add_argument("--output", default="experiments/results", help="output directory")
    bench.add_argument("--episodes", type=int, default=1000, help="episodes per scenario per policy")
    bench.add_argument("--seed", type=int, default=20260911)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.command == "benchmark":
        aggregate = run_benchmark(Path(args.output), episodes_per_scenario=args.episodes, seed=args.seed)
        print(json.dumps(aggregate, indent=2))


if __name__ == "__main__":
    main()
