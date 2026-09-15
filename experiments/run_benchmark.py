from pathlib import Path
from llm_parkinsonism.simulation import run_benchmark

if __name__ == "__main__":
    out = Path("experiments/results")
    results = run_benchmark(out, episodes_per_scenario=1000, seed=20260911)
    for row in results:
        print(row)
