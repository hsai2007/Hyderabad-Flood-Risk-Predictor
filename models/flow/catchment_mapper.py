import geopandas as gpd
import pandas as pd
from shapely.geometry import Point
import numpy as np

# Load land use
land = gpd.read_file("data/hyderabad_landuse.geojson")

# Re-run classification logic
def classify(row):
    if row.get("landuse") in ["residential"]:
        return "residential"
    if row.get("landuse") in ["commercial", "retail"]:
        return "commercial"
    if row.get("landuse") in ["industrial"]:
        return "industrial"
    if row.get("leisure") == "park":
        return "park"
    if row.get("natural") in ["grass","wood","forest"]:
        return "forest"
    if row.get("natural") == "water":
        return "water"
    return None

land["land_type"] = land.apply(classify, axis=1)
land = land.dropna(subset=["land_type"])

land = land.to_crs(epsg=3857)
land["area_m2"] = land.geometry.area

# Load drain nodes
nodes = pd.read_csv("data/drain_nodes.csv")
nodes_gdf = gpd.GeoDataFrame(
    nodes,
    geometry=gpd.points_from_xy(nodes.x, nodes.y),
    crs="EPSG:3857"
)

# Find nearest drain node for each land polygon
def nearest_node(poly):
    c = poly.centroid
    dists = nodes_gdf.geometry.distance(c)
    return nodes_gdf.iloc[dists.idxmin()].node_id

land["node_id"] = land.geometry.apply(nearest_node)

# Save catchment table
land[["node_id","land_type","area_m2"]].to_csv("data/node_catchments.csv", index=False)

print("[SUCCESS] Land assigned to drain nodes")
