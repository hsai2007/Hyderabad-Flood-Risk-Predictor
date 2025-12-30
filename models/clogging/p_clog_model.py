import pandas as pd
import numpy as np

pipes = pd.read_csv("data/drain_design.csv")

# ----------------------------------------
# Clogging probability model
# ----------------------------------------

def clog_probability(D, Q):
    # Smaller pipes clog more
    size_factor = np.exp(-D)

    # Low velocity → more clogging
    velocity = Q / (np.pi * (D/2)**2)
    vel_factor = np.exp(-velocity)

    # Combine
    p = 0.7*size_factor + 0.3*vel_factor
    return min(max(p, 0), 1)

pipes["P_clog"] = pipes.apply(
    lambda r: clog_probability(r["required_diameter_m"], r["flow_m3s"]),
    axis=1
)

# Effective capacity
pipes["Q_effective"] = pipes["flow_m3s"] * (1 - pipes["P_clog"])

# Failure condition
pipes["flooding"] = pipes["flow_m3s"] > pipes["Q_effective"]

pipes.to_csv("data/flood_risk.csv", index=False)

print("[SUCCESS] Flood risk computed")
print(pipes[["from","to","flow_m3s","required_diameter_m","P_clog","flooding"]].head())
