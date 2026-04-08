import geopandas as gpd
import pandas as pd
import numpy as np
from shapely.geometry import Point

# ================================
# Load and classify land use
# ================================
print("[INFO] Loading land use data...")
land = gpd.read_file("data/hyderabad_landuse.geojson")

def classify(row):
    if row.get("landuse") in ["residential"]:
        return "residential"
    if row.get("landuse") in ["commercial", "retail"]:
        return "commercial"
    if row.get("landuse") in ["industrial"]:
        return "industrial"
    if row.get("leisure") == "park":
        return "park"
    if row.get("natural") in ["grass", "wood", "forest"]:
        return "forest"
    if row.get("natural") == "water":
        return "water"
    return None

land["land_type"] = land.apply(classify, axis=1)
land = land.dropna(subset=["land_type"])
land = land.to_crs(epsg=3857)
land["area_m2"] = land.geometry.area

# ================================
# Load drain nodes
# ================================
nodes = pd.read_csv("data/drain_nodes.csv")
nodes_gdf = gpd.GeoDataFrame(
    nodes,
    geometry=gpd.points_from_xy(nodes.x, nodes.y),
    crs="EPSG:3857"
)

print(f"[INFO] Total drain nodes: {len(nodes_gdf)}")

# ================================
# Assign each land polygon to nearest node
# ================================
print("[INFO] Assigning land polygons to nearest nodes...")

def nearest_node(poly):
    c = poly.centroid
    dists = nodes_gdf.geometry.distance(c)
    return nodes_gdf.iloc[dists.idxmin()].node_id

land["node_id"] = land.geometry.apply(nearest_node)
mapped = land[["node_id", "land_type", "area_m2"]].copy()

# ================================
# Find nodes with no land polygon assigned
# ================================
mapped_node_ids = set(mapped["node_id"].unique())
all_node_ids = set(nodes["node_id"].tolist())
unmapped_ids = all_node_ids - mapped_node_ids

print(f"[INFO] Nodes with OSM land data:  {len(mapped_node_ids)}")
print(f"[INFO] Nodes with no land data:   {len(unmapped_ids)}")

# ================================
# Assign default catchment to unmapped nodes
# ================================
# In Hyderabad urban areas, average inter-node spacing is ~300-500m
# A node typically drains a circle of radius ~250m = ~196,000 m2
# We assume mixed urban (60% residential, 40% road/commercial)
# This is consistent with CPHEEO Manual default for ungauged urban areas

DEFAULT_AREA_M2 = 150000  # 150,000 m2 = 15 hectares per node
DEFAULT_LAND_TYPE = "residential"  # conservative — higher runoff coefficient

default_records = []
for node_id in unmapped_ids:
    default_records.append({
        "node_id": node_id,
        "land_type": DEFAULT_LAND_TYPE,
        "area_m2": DEFAULT_AREA_M2
    })

default_df = pd.DataFrame(default_records)
print(f"[INFO] Assigned default catchment ({DEFAULT_AREA_M2/1000:.0f}k m2) to {len(default_records)} unmapped nodes")

# ================================
# Combine and save
# ================================
catchments = pd.concat([mapped, default_df], ignore_index=True)
catchments.to_csv("data/node_catchments.csv", index=False)

print(f"\n[SUCCESS] Catchment mapping complete")
print(f"  Total nodes with catchments: {catchments['node_id'].nunique()}")
print(f"  OSM-mapped nodes: {len(mapped_node_ids)}")
print(f"  Default-assigned nodes: {len(unmapped_ids)}")
print(f"\nLand type distribution:")
print(catchments.groupby('land_type')['area_m2'].agg(['count','sum']).round(0))