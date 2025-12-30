import geopandas as gpd
import pandas as pd

drains = gpd.read_file("data/hyderabad_drains.geojson")
risk = pd.read_csv("data/flood_risk.csv")

# Join on from→to is tricky; we match by index
drains = drains.reset_index().rename(columns={"index":"edge_id"})
risk["edge_id"] = risk.index

merged = drains.merge(risk, on="edge_id")

# Keep flooded only
flooded = merged[merged["flooding"] == True]

flooded.to_file("data/flooded_drains.geojson", driver="GeoJSON")

print("[SUCCESS] Flood risk map created → data/flooded_drains.geojson")
