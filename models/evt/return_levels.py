import pandas as pd
import numpy as np
from scipy.stats import gumbel_r

# Load fitted Gumbel parameters
params = pd.read_csv("data/rainfall/gumbel_params.csv")

mu = params.loc[0, "mu"]
beta = params.loc[0, "beta"]

print("[INFO] Loaded Gumbel parameters")
print("μ =", mu)
print("β =", beta)

# Return periods (years)
return_periods = [10, 25, 50, 100]

results = []

for T in return_periods:
    p = 1 - 1/T  # exceedance probability
    x = gumbel_r.ppf(p, loc=mu, scale=beta)
    results.append([T, x])

df = pd.DataFrame(results, columns=["return_period_years", "rainfall_mm_3hr"])

df.to_csv("data/rainfall/return_levels.csv", index=False)

print("\n[RESULT] Extreme rainfall return levels:")
print(df)
print("\n[SUCCESS] data/rainfall/return_levels.csv created")
