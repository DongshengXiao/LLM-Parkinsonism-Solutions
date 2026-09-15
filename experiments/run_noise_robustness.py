from llm_parkinsonism.simulation import run_noise_robustness, run_soft_value_probe

if __name__ == "__main__":
    rows = run_noise_robustness("experiments/results/noise_robustness.csv", episodes_per_scenario=150, seed=20260911)
    for row in rows:
        print(row)
    print("beneficial-soft probe:", run_soft_value_probe())
