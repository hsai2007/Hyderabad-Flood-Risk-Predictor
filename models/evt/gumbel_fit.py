import pandas as pd
import numpy as np
from scipy.stats import gumbel_r

# ================================
# Config
# ================================
INPUT_FILE = "data/rainfall/extreme_events.csv"

print("[INFO] Loading extreme rainfall data...")

df = pd.read_csv(INPUT_FILE)
data = df["rain_3hr"].values

print("[INFO] Number of years:", len(data))
print("[INFO] Max observed 3-hour storm:", np.max(data), "mm")

# ================================
# Fit Gumbel
# ================================
print("\n[INFO] Fitting Gumbel distribution...")

mu, beta = gumbel_r.fit(data)

print(f"[INFO] Gumbel parameters:")
print(f"  Location (μ) = {mu:.2f}")
print(f"  Scale (β)    = {beta:.2f}")

# Save parameters
params = pd.DataFrame([[mu, beta]], columns=["mu", "beta"])
params.to_csv("data/rainfall/gumbel_params.csv", index=False)

print("\n[SUCCESS] Gumbel parameters saved to data/rainfall/gumbel_params.csv")
