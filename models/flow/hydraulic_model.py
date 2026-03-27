import pandas as pd
import numpy as np

# ------------------------------
# FIX: Load EVT storm dynamically — don't hardcode 35.4mm
# The Gumbel model computes this from actual data, so use it.
# ------------------------------
evt = pd.read_csv("data/rainfall/return_levels.csv")
RAIN_3HR = evt.loc[evt["return_period_years"] == 100, "rainfall_mm_3hr"].values[0]
INTENSITY = RAIN_3HR / 3   # mm/hr average intensity

print(f"[INFO] 100-year storm: {RAIN_3HR:.1f} mm in 3 hours ({INTENSITY:.1f} mm/hr avg)")

# ------------------------------
# Load land use
# ------------------------------
land = pd.read_csv("data/land_use.csv")

# ------------------------------
# Convert rainfall to runoff: Q = C × I × A
# 1 mm/hr on 1 km² = 1,000,000 m² × 0.001 m/hr = 1000 m³/hr = 1000/3600 m³/s
# ------------------------------
def runoff_m3s(C, I_mm_hr, A_km2):
    return (C * I_mm_hr * A_km2 * 1000) / 3600

land["runoff_m3s"] = land.apply(
    lambda r: runoff_m3s(r["runoff_C"], INTENSITY, r["area_km2"]),
    axis=1
)

# ------------------------------
# Print summary
# ------------------------------
print("\n[100-YEAR STORM RUNOFF BY SURFACE TYPE]")
print(land[["land_type", "area_km2", "runoff_C", "runoff_m3s"]].to_string(index=False))

print(f"\n[TOTAL PEAK FLOW ENTERING DRAINS]: {land['runoff_m3s'].sum():.2f} m³/s")
print("Note: This is a simplified aggregate. Node-level model (node_runoff.py)")
print("      applies time-of-concentration corrections per catchment.")
