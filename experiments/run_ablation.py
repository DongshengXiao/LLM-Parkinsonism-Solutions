from llm_parkinsonism.simulation import run_ablation

if __name__ == "__main__":
    rows = run_ablation("experiments/results/ablation.csv", episodes_per_scenario=300, seed=20260911)
    for row in rows:
        print(row)
