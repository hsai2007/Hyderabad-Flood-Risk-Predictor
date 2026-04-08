import geopandas as gpd
import pandas as pd

print("[INFO] Building risk-annotated GeoJSON...")

# Load original drain geometries
drains = gpd.read_file("data/hyderabad_drains.geojson")
drains = drains.reset_index().rename(columns={"index": "edge_id"})

# Load graph edges — gives us from/to for each edge_id
edges = pd.read_csv("data/drain_edges.csv").reset_index().rename(columns={"index": "edge_id"})

# Load flood risk — now contains ALL pipes including rivers
risk = pd.read_csv("data/flood_risk.csv")

# Step 1 — attach from/to to each drain geometry
drains = drains.merge(edges[["edge_id", "from", "to"]], on="edge_id", how="left")

# Step 2 — attach risk data via from/to pair
drains = drains.merge(risk, on=["from", "to"], how="left")

# Step 3 — assign risk color
def risk_color(row):
    # Unmatched geometry — truly no data
    if pd.isna(row.get("flow_m3s")):
        return "gray"
    # River or major canal
    if row.get("is_river") == True:
        return "purple"
    # Zero flow boundary node
    if row.get("flow_m3s", 0) == 0:
        return "gray"
    # Flooded urban drain
    if row.get("flooding") == True:
        return "red"
    # Clog risk levels
    p = row.get("P_clog", 0)
    if pd.isna(p):  return "gray"
    if p > 0.5:     return "orange"
    if p > 0.2:     return "yellow"
    return "green"

drains["risk_color"]   = drains.apply(risk_color, axis=1)
drains["flow_m3s"]     = drains["flow_m3s"].fillna(0).round(3)
drains["overflow_m3s"] = drains["overflow_m3s"].fillna(0).round(3)
drains["P_clog"]       = drains["P_clog"].fillna(0).round(3)
drains["is_river"]     = drains["is_river"].fillna(False)
drains["flooding"]     = drains["flooding"].fillna(False)

# Step 4 — save
drains.to_file("data/drain_risk.geojson", driver="GeoJSON")

colors = drains["risk_color"].value_counts()
print(f"\n[SUCCESS] Risk GeoJSON built")
print(f"  Total pipes:           {len(drains)}")
print(f"  Flooded (red):         {colors.get('red', 0)}")
print(f"  High clog (orange):    {colors.get('orange', 0)}")
print(f"  Medium clog (yellow):  {colors.get('yellow', 0)}")
print(f"  Low risk (green):      {colors.get('green', 0)}")
print(f"  Waterway (purple):     {colors.get('purple', 0)}")
print(f"  No data (gray):        {colors.get('gray', 0)}")