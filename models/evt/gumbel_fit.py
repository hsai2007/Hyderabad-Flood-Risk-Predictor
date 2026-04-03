import pandas as pd
import numpy as np
from scipy.stats import genextreme

INPUT_FILE = "data/rainfall/extreme_events.csv"

print("[INFO] Loading extreme rainfall data...")
df = pd.read_csv(INPUT_FILE)
data = df["rain_3hr"].values

print("[INFO] Number of years:", len(data))
print("[INFO] Max observed 3-hour storm:", np.max(data), "mm")

print("\n[INFO] Fitting GEV distribution...")
shape, mu, beta = genextreme.fit(data)
xi = -shape

print(f"[INFO] GEV parameters:")
print(f"  Location (μ) = {mu:.4f}")
print(f"  Scale    (β) = {beta:.4f}")
print(f"  Shape    (ξ) = {xi:.4f}")

if xi > 0.05:
    print("  → Heavy tail: rare events MORE extreme than Gumbel predicts")
elif xi < -0.05:
    print("  → Light tail: rare events LESS extreme than Gumbel predicts")
else:
    print("  → Near-zero shape: GEV ≈ Gumbel for this data")

params = pd.DataFrame([[mu, beta, xi]], columns=["mu", "beta", "xi"])
params.to_csv("data/rainfall/gumbel_params.csv", index=False)
print("\n[SUCCESS] GEV parameters saved")