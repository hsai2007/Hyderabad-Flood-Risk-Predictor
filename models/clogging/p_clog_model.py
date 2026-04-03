import pandas as pd
import numpy as np

pipes = pd.read_csv("data/drain_design.csv")

# Remove zero flow pipes
pipes = pipes[pipes["flow_m3s"] > 0].copy()
print(f"[INFO] Pipes with actual flow: {len(pipes)}")
# Remove pipes with river-scale flows — these are Musi River
# and major canals, not urban drains
pipes = pipes[pipes["flow_m3s"] < 15.0].copy()
print(f"[INFO] Pipes after removing river-scale flows: {len(pipes)}")

# ================================
# REALISTIC PIPE SIZING
# design_pipes.py gave every pipe a perfect diameter — so nothing floods.
# Real Hyderabad drains were built years ago with standard fixed sizes.
# Diameters assigned per CPHEEO Manual on Storm Water Drainage
# design standards for Class I cities.
# ================================

def realistic_diameter(flow):
    """
    Pipe diameters scaled to Hyderabad network flow magnitudes.
    Per CPHEEO Manual on Storm Water Drainage for Class I cities.
    Large trunk drains in Hyderabad carry 10-80 m3/s during peak monsoon.
    """
    if flow < 0.05:    return 0.45
    elif flow < 0.3:   return 0.60
    elif flow < 1.0:   return 0.90
    elif flow < 3.0:   return 1.20
    elif flow < 8.0:   return 1.80
    elif flow < 15.0:  return 2.40
    else:              return 3.00

def manning_capacity(D, S, n=0.013):
    A = np.pi * (D / 2) ** 2
    R = D / 4
    Q_full = (1 / n) * A * (R ** (2/3)) * (max(S, 0.005) ** 0.5)
    return Q_full * 0.75

pipes["required_diameter_m"] = pipes["flow_m3s"].apply(realistic_diameter)
pipes["design_capacity_m3s"] = pipes.apply(
    lambda r: manning_capacity(r["required_diameter_m"], r["slope"]),
    axis=1
)

print("[INFO] Pipe diameter distribution:")
print(pipes["required_diameter_m"].value_counts().sort_index())

# ================================
# CLOGGING MODEL
# Based on CPHEEO Manual — self cleansing velocity = 0.6 m/s
# ================================

def flow_velocity(Q, D):
    A = np.pi * (D / 2) ** 2
    if A <= 0 or Q <= 0:
        return 0.0
    return Q / A

def clogging_capacity_factor(D, velocity):
    if D < 0.30:
        max_reduction = 0.60
    elif D < 0.60:
        max_reduction = 0.45
    else:
        max_reduction = 0.20

    V_SELF_CLEANSE = 0.6
    if velocity >= V_SELF_CLEANSE:
        vel_factor = 0.0
    else:
        vel_factor = 1.0 - (velocity / V_SELF_CLEANSE)

    total_reduction = max_reduction * vel_factor
    return max(1.0 - total_reduction, 0.0)

pipes["velocity_m_s"] = pipes.apply(
    lambda r: flow_velocity(r["flow_m3s"], r["required_diameter_m"]),
    axis=1
)

pipes["capacity_factor"] = pipes.apply(
    lambda r: clogging_capacity_factor(r["required_diameter_m"], r["velocity_m_s"]),
    axis=1
)

pipes["effective_capacity_m3s"] = pipes["design_capacity_m3s"] * pipes["capacity_factor"]
pipes["P_clog"] = 1.0 - pipes["capacity_factor"]
pipes["flooding"] = pipes["flow_m3s"] > pipes["effective_capacity_m3s"]
pipes["overflow_m3s"] = (pipes["flow_m3s"] - pipes["effective_capacity_m3s"]).clip(lower=0)

pipes.to_csv("data/flood_risk.csv", index=False)

flooded_count = pipes["flooding"].sum()
print(f"\n[SUCCESS] Flood risk computed")
print(f"  Total pipes:   {len(pipes)}")
print(f"  Flooded pipes: {flooded_count} ({100 * flooded_count / len(pipes):.1f}%)")
print(f"  Avg P_clog:    {pipes['P_clog'].mean():.1%}")
print()
print(pipes[[
    "from", "to", "flow_m3s",
    "required_diameter_m", "velocity_m_s",
    "P_clog", "effective_capacity_m3s", "flooding"
]].head(10))