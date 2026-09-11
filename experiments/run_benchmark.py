"""Reproduce the main controlled synthetic benchmark."""

from llm_parkinsonism.simulation import run_benchmark


if __name__ == "__main__":
    run_benchmark("experiments/results", episodes_per_scenario=2000, seed=20260911)
