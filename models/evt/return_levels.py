import pandas as pd
import numpy as np
from scipy.stats import genextreme

params = pd.read_csv("data/rainfall/gumbel_params.csv")
mu   = params.loc[0, "mu"]
beta = params.loc[0, "beta"]
xi   = params.loc[0, "xi"]

print("[INFO] Loaded GEV parameters")
print(f"  μ = {mu:.4f},  β = {beta:.4f},  ξ = {xi:.4f}")

return_periods = [10, 25, 50, 100]
results = []

for T in return_periods:
    p = 1 - 1/T
    x = genextreme.ppf(p, -xi, loc=mu, scale=beta)
    results.append([T, round(x, 3)])

df = pd.DataFrame(results, columns=["return_period_years", "rainfall_mm_3hr"])
df.to_csv("data/rainfall/return_levels.csv", index=False)

print("\n[RESULT] GEV-based return levels:")
print(df)
print("\n[SUCCESS] data/rainfall/return_levels.csv created")