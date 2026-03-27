import pandas as pd
import numpy as np

# ================================
# Load 100-year storm from EVT
# ================================
evt = pd.read_csv("data/rainfall/return_levels.csv")
RAIN_3HR = evt.loc[evt["return_period_years"] == 100, "rainfall_mm_3hr"].values[0]

print("[INFO] Using 100-year EVT rainfall:", RAIN_3HR, "mm in 3 hours")

# ================================
# Runoff coefficients (standard values)
# ================================
C = {
    "road":        0.9,
    "commercial":  0.8,
    "industrial":  0.7,
    "residential": 0.6,
    "park":        0.3,
    "forest":      0.2,
    "water":       0.1   # FIX: water bodies can overflow, not 0.0
}

# ================================
# Load catchment data
# ================================
catch = pd.read_csv("data/node_catchments.csv")
catch["C"] = catch["land_type"].map(C)

# ================================
# FIX: Time of Concentration (Tc)
# ================================
# The Rational Method Q = C*I*A is only valid when storm duration = Tc.
# Larger catchments have longer Tc and lower peak intensity.
# We use the Kirpich formula: Tc (min) = 0.0195 * L^0.77 * S^(-0.385)
# L estimated as sqrt(Area), typical urban slope S = 0.005

# Base 1-hour intensity (assume 40% of 3hr rain falls in peak 1hr — standard India monsoon)
I_1hr = RAIN_3HR * 0.40  # mm in 1 hour

SLOPE_TYPICAL = 0.005  # typical urban slope

def time_of_concentration_minutes(area_m2, slope=SLOPE_TYPICAL):
    """Kirpich formula — returns Tc in minutes."""
    L = np.sqrt(area_m2)
    Tc = 0.0195 * (L ** 0.77) * (slope ** -0.385)
    return max(Tc, 5.0)  # minimum 5 minutes

def intensity_for_Tc(Tc_minutes, I_1hr_mm):
    """Sherman IDF formula — returns intensity in mm/hr."""
    I = I_1hr_mm * ((Tc_minutes / 60.0) ** -0.65)
    return max(I, RAIN_3HR / 3.0)  # floor at 3hr average intensity

# ================================
# Compute runoff per node with Tc
# ================================
node_groups = catch.groupby("node_id")
records = []

for node_id, group in node_groups:
    total_area_m2 = group["area_m2"].sum()
    C_avg = (group["C"] * group["area_m2"]).sum() / total_area_m2
    Tc = time_of_concentration_minutes(total_area_m2)
    intensity_mm_hr = intensity_for_Tc(Tc, I_1hr)
    Q = (C_avg * intensity_mm_hr * total_area_m2 / 1000.0) / 3600.0

    records.append({
        "node_id": node_id,
        "area_m2": total_area_m2,
        "C_weighted": round(C_avg, 3),
        "Tc_minutes": round(Tc, 1),
        "intensity_mm_hr": round(intensity_mm_hr, 2),
        "runoff_m3s": Q
    })

node_Q = pd.DataFrame(records)
node_Q.to_csv("data/node_runoff.csv", index=False)

print("[SUCCESS] Node runoff computed with time-of-concentration correction")
print(node_Q.head())
