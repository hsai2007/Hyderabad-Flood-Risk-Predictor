import pandas as pd
import numpy as np
from scipy.optimize import brentq

# Manning's roughness for concrete drains
n = 0.013

pipes = pd.read_csv("data/pipe_flows.csv")
edges = pd.read_csv("data/drain_edges_with_slope.csv")

pipes = pipes.merge(edges, on=["from","to"])

# ================================
# FIX: Pipes designed at 75% full capacity, not 100% full
# ================================
# Engineering practice: urban drains are sized so that the design
# flow runs at ~75% of the full-pipe capacity. This:
#   1. Provides a safety margin for flows exceeding the design storm
#   2. Maintains ventilation (pipes shouldn't run surcharged normally)
#   3. Accounts for minor clogging without immediate flooding
#
# At 75% full (y/D = 0.75), the hydraulic properties change:
#   - Flow area A = D²/8 * (θ - sinθ) where θ = 2*arccos(1 - 2*y/D)
#   - Wetted perimeter P = D/2 * θ
#   - Hydraulic radius R = A / P
#
# We solve Manning's Q for partial depth y/D = 0.75.

FILL_RATIO = 0.75  # design pipes to carry flow at 75% full

def partial_flow_properties(D, fill_ratio):
    """
    Compute area (A) and hydraulic radius (R) for a circular pipe
    at a given fill ratio (y/D).
    """
    y = fill_ratio * D
    # Central angle (radians) subtended by the water surface
    theta = 2 * np.arccos(1 - 2 * y / D)
    A = (D**2 / 8) * (theta - np.sin(theta))
    P = (D / 2) * theta
    R = A / P
    return A, R

def manning_Q_partial(D, S, fill_ratio=FILL_RATIO):
    """Manning's Q for a partially-full circular pipe."""
    A, R = partial_flow_properties(D, fill_ratio)
    return (1 / n) * A * (R ** (2/3)) * (S ** 0.5)

def solve_D(Q, S):
    """Find minimum pipe diameter D (metres) to carry flow Q at 75% full."""
    if Q < 0.001:
        return 0.15  # minimum practical drain size = 150mm

    # Check if a very large pipe is needed
    Q_max_check = manning_Q_partial(5.0, S)
    if Q > Q_max_check:
        return 5.0  # cap at 5m diameter (box culvert territory)

    # Brentq is more robust than fsolve for this monotonic function
    try:
        D = brentq(lambda D: manning_Q_partial(D, S) - Q, 0.05, 5.0)
    except ValueError:
        D = 5.0  # fallback

    # Round up to nearest standard pipe size (100mm increments)
    standard_sizes = np.arange(0.15, 5.1, 0.10)
    D_standard = standard_sizes[standard_sizes >= D][0]
    return D_standard

pipes["required_diameter_m"] = pipes.apply(
    lambda r: solve_D(r["flow_m3s"], r["slope"]),
    axis=1
)

# Also compute actual full-pipe capacity for reference
pipes["full_capacity_m3s"] = pipes.apply(
    lambda r: manning_Q_partial(r["required_diameter_m"], r["slope"], fill_ratio=1.0),
    axis=1
)

pipes["design_capacity_m3s"] = pipes.apply(
    lambda r: manning_Q_partial(r["required_diameter_m"], r["slope"], fill_ratio=FILL_RATIO),
    axis=1
)

pipes.to_csv("data/drain_design.csv", index=False)

print("[SUCCESS] Drain sizes computed at 75% fill ratio (engineering standard)")
print(pipes[["from","to","flow_m3s","required_diameter_m","design_capacity_m3s"]].head())
