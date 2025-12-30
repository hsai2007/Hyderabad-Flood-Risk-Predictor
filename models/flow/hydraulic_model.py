import pandas as pd

# ------------------------------
# Load EVT storm (100-year)
# ------------------------------
RAIN_3HR = 35.4  # mm from Gumbel
INTENSITY = RAIN_3HR / 3   # mm/hr

# ------------------------------
# Load land use
# ------------------------------
land = pd.read_csv("data/land_use.csv")

# ------------------------------
# Convert rainfall to runoff
# Q = C × I × A
# ------------------------------
def runoff_m3s(C, I, A):
    # 1 mm on 1 km² = 1000 m³
    return (C * I * A * 1000) / 3600

land["runoff_m3s"] = land.apply(
    lambda r: runoff_m3s(r["runoff_C"], INTENSITY, r["area_km2"]),
    axis=1
)

# ------------------------------
# Print summary
# ------------------------------
print("\n[100-YEAR STORM RUNOFF BY SURFACE]")
print(land[["land_type","area_km2","runoff_C","runoff_m3s"]])

print("\n[TOTAL WATER ENTERING DRAINS]")
print(land["runoff_m3s"].sum(), "m³/s")
