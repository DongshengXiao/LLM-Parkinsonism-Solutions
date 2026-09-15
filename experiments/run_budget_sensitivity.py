from llm_parkinsonism.simulation import run_budget_sensitivity

if __name__ == "__main__":
    rows = run_budget_sensitivity("experiments/results/budget_sensitivity.csv", episodes_per_scenario=150, seed=20260911)
    for row in rows:
        print(row)
