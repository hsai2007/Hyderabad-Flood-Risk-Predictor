import pandas as pd
import numpy as np

pipes = pd.read_csv("data/drain_design.csv")
print(f"[INFO] Total pipes loaded: {len(pipes)}")

# ================================
# SEPARATE river-scale pipes from urban drains
# instead of dropping them entirely
# ================================

pipes["is_river"] = (pipes["flow_m3s"] > 40.0) | (pipes["flow_m3s"] == 0)

urban  = pipes[~pipes["is_river"]].copy()
rivers = pipes[pipes["is_river"]].copy()

print(f"[INFO] Urban drain pipes (to analyse): {len(urban)}")
print(f"[INFO] River/zero pipes (excluded):    {len(rivers)}")

# ================================
# REALISTIC PIPE SIZING
# Diameters per CPHEEO Manual on Storm Water Drainage
# for Class I cities — assigned by flow magnitude
# ================================

def realistic_diameter(flow):
    if flow < 0.05:   return 0.45
    elif flow < 0.3:  return 0.60
    elif flow < 1.0:  return 0.90
    elif flow < 3.0:  return 1.20
    elif flow < 8.0:  return 1.80
    elif flow < 15.0: return 2.40
    else:             return 3.00

def manning_capacity(D, S, n=0.013):
    """Manning's equation at 75% full — CPHEEO standard."""
    A = np.pi * (D / 2) ** 2
    R = D / 4
    Q_full = (1 / n) * A * (R ** (2/3)) * (max(S, 0.005) ** 0.5)
    return Q_full * 0.75

urban["required_diameter_m"] = urban["flow_m3s"].apply(realistic_diameter)
urban["design_capacity_m3s"] = urban.apply(
    lambda r: manning_capacity(r["required_diameter_m"], r["slope"]),
    axis=1
)

print("[INFO] Pipe diameter distribution:")
print(urban["required_diameter_m"].value_counts().sort_index())

# ================================
# CLOGGING MODEL
# CPHEEO Manual — self-cleansing velocity = 0.6 m/s
# ================================

def flow_velocity(Q, D):
    A = np.pi * (D / 2) ** 2
    if A <= 0 or Q <= 0:
        return 0.0
    return Q / A

def clogging_capacity_factor(D, velocity):
    if D < 0.45:
        max_reduction = 0.60
    elif D < 0.90:
        max_reduction = 0.45
    else:
        max_reduction = 0.20

    V_SELF_CLEANSE = 0.6
    if velocity >= V_SELF_CLEANSE:
        vel_factor = 0.0
    else:
        vel_factor = 1.0 - (velocity / V_SELF_CLEANSE)

    return max(1.0 - (max_reduction * vel_factor), 0.0)

urban["velocity_m_s"] = urban.apply(
    lambda r: flow_velocity(r["flow_m3s"], r["required_diameter_m"]),
    axis=1
)

urban["capacity_factor"] = urban.apply(
    lambda r: clogging_capacity_factor(r["required_diameter_m"], r["velocity_m_s"]),
    axis=1
)

urban["effective_capacity_m3s"] = urban["design_capacity_m3s"] * urban["capacity_factor"]
urban["P_clog"]       = 1.0 - urban["capacity_factor"]
urban["flooding"]     = urban["flow_m3s"] > urban["effective_capacity_m3s"]
urban["overflow_m3s"] = (urban["flow_m3s"] - urban["effective_capacity_m3s"]).clip(lower=0)

# ================================
# Give river/zero pipes neutral values
# ================================
rivers["required_diameter_m"]    = 0.0
rivers["design_capacity_m3s"]    = 0.0
rivers["velocity_m_s"]           = 0.0
rivers["capacity_factor"]        = 0.0
rivers["effective_capacity_m3s"] = 0.0
rivers["P_clog"]                 = 0.0
rivers["flooding"]               = False
rivers["overflow_m3s"]           = 0.0

# ================================
# Recombine and save ALL pipes
# ================================
all_pipes = pd.concat([urban, rivers], ignore_index=True)
all_pipes.to_csv("data/flood_risk.csv", index=False)

flooded_count = urban["flooding"].sum()
print(f"\n[SUCCESS] Flood risk computed")
print(f"  Urban pipes analysed: {len(urban)}")
print(f"  Flooded pipes:        {flooded_count} ({100 * flooded_count / len(urban):.1f}%)")
print(f"  River/zero pipes:     {len(rivers)}")
print(f"  Total saved:          {len(all_pipes)}")
print()
print(urban[[
    "from", "to", "flow_m3s",
    "required_diameter_m", "velocity_m_s",
    "P_clog", "effective_capacity_m3s", "flooding"
]].head(10))