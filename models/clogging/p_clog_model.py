import pandas as pd
import numpy as np

pipes = pd.read_csv("data/drain_design.csv")

# ================================
# FIX: Replace invented clogging model with physically grounded approach
# ================================
#
# ORIGINAL BUG: The old model computed P_clog then set:
#   Q_effective = flow_m3s * (1 - P_clog)
# and checked: flow_m3s > Q_effective
# This ALWAYS returns True (flooding everywhere) because Q_effective < flow_m3s
# by construction. That's not a flood model — it's a tautology.
#
# CORRECT APPROACH:
# 1. The pipe is DESIGNED to carry flow_m3s at 75% full (from design_pipes.py)
#    So design_capacity_m3s >= flow_m3s by definition (no clogging → no flood)
#
# 2. Clogging REDUCES the effective capacity below design capacity.
#    We model this as a capacity reduction factor based on:
#      a) Pipe diameter — smaller pipes are more vulnerable to blockage
#      b) Flow velocity — low velocity allows sediment/debris to settle
#
# 3. Flooding occurs when: flow_m3s > capacity_after_clogging
#    i.e. when the clogging reduction is severe enough that the pipe
#    can no longer pass its design flow.
#
# Clogging capacity reduction (based on drainage engineering guidelines):
#   - Pipes < 300mm: up to 60% capacity reduction from debris
#   - Pipes 300–600mm: up to 35% reduction
#   - Pipes > 600mm: up to 15% reduction (large enough to pass most debris)
#
# Velocity threshold (CPHEEO Manual on Sewerage):
#   - Self-cleansing velocity = 0.6 m/s minimum
#   - Below this, sediment settles and blockage risk increases sharply

def flow_velocity(Q, D):
    """Mean flow velocity in pipe at design flow (m/s)."""
    A = np.pi * (D / 2) ** 2
    if A <= 0 or Q <= 0:
        return 0.0
    return Q / A

def clogging_capacity_factor(D, velocity):
    """
    Returns the fraction of design capacity remaining after clogging.
    Factor < 1 means clogging reduces capacity.
    Based on pipe diameter vulnerability and velocity self-cleansing.
    """
    # Size-based maximum clogging reduction
    if D < 0.30:
        max_reduction = 0.60   # small pipes: up to 60% capacity lost
    elif D < 0.60:
        max_reduction = 0.35   # medium pipes
    else:
        max_reduction = 0.15   # large pipes

    # Velocity factor: below self-cleansing velocity (0.6 m/s), clogging worsens
    V_SELF_CLEANSE = 0.6  # m/s (CPHEEO standard)
    if velocity >= V_SELF_CLEANSE:
        vel_factor = 0.0   # adequate velocity — minimal clogging
    else:
        # Linear interpolation: at v=0 → full clogging risk, at v=0.6 → no risk
        vel_factor = 1.0 - (velocity / V_SELF_CLEANSE)

    # Total capacity reduction
    total_reduction = max_reduction * vel_factor

    # Remaining capacity factor (e.g. 0.7 means pipe carries 70% of design flow)
    return max(1.0 - total_reduction, 0.0)

# ================================
# Compute clogging and flood risk
# ================================
pipes["velocity_m_s"] = pipes.apply(
    lambda r: flow_velocity(r["flow_m3s"], r["required_diameter_m"]),
    axis=1
)

pipes["capacity_factor"] = pipes.apply(
    lambda r: clogging_capacity_factor(r["required_diameter_m"], r["velocity_m_s"]),
    axis=1
)

# Effective capacity after clogging (compared against DESIGN capacity, not flow)
pipes["effective_capacity_m3s"] = pipes["design_capacity_m3s"] * pipes["capacity_factor"]

# P_clog: probability of clogging (for display/reporting only)
# Expressed as 1 - capacity_factor for clarity
pipes["P_clog"] = 1.0 - pipes["capacity_factor"]

# Flooding: demand exceeds what the (clogged) pipe can actually carry
pipes["flooding"] = pipes["flow_m3s"] > pipes["effective_capacity_m3s"]

# Flood severity: how much flow exceeds capacity (m³/s overflow)
pipes["overflow_m3s"] = (pipes["flow_m3s"] - pipes["effective_capacity_m3s"]).clip(lower=0)

pipes.to_csv("data/flood_risk.csv", index=False)

flooded_count = pipes["flooding"].sum()
print(f"[SUCCESS] Flood risk computed")
print(f"  Total pipes: {len(pipes)}")
print(f"  Flooded pipes: {flooded_count} ({100*flooded_count/len(pipes):.1f}%)")
print(pipes[["from","to","flow_m3s","required_diameter_m","velocity_m_s","P_clog","effective_capacity_m3s","flooding"]].head())
