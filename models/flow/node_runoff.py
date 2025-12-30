import pandas as pd

# ================================
# Load 100-year storm from EVT
# ================================
evt = pd.read_csv("data/rainfall/return_levels.csv")
RAIN_3HR = evt.loc[evt["return_period_years"] == 100, "rainfall_mm_3hr"].values[0]

INTENSITY = RAIN_3HR / 3   # mm/hr

print("[INFO] Using 100-year EVT rainfall:", RAIN_3HR, "mm in 3 hours")

# Runoff coefficients
C = {
    "road": 0.9,
    "commercial": 0.8,
    "industrial": 0.7,
    "residential": 0.6,
    "park": 0.3,
    "forest": 0.2,
    "water": 0.0
}

catch = pd.read_csv("data/node_catchments.csv")

catch["C"] = catch["land_type"].map(C)

# Convert mm/hr × m² → m³/s
catch["runoff_m3s"] = (catch["C"] * INTENSITY * catch["area_m2"] / 1000) / 3600

node_Q = catch.groupby("node_id")["runoff_m3s"].sum().reset_index()
node_Q.to_csv("data/node_runoff.csv", index=False)

print("[SUCCESS] Node runoff computed from EVT rainfall")
