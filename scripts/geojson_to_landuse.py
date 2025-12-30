import geopandas as gpd
import pandas as pd

# Load GeoJSON
gdf = gpd.read_file("data/hyderabad_landuse.geojson")

print("[INFO] Columns found:", gdf.columns)

# ---------------------------------
# Separate roads (LINE features)
# ---------------------------------
roads = gdf[gdf["highway"].notna()].copy()

# Remove roads from main landuse set
gdf = gdf[gdf["highway"].isna()]

# ---------------------------------
# Classify land use (polygons only)
# ---------------------------------
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

gdf["land_type"] = gdf.apply(classify, axis=1)
gdf = gdf.dropna(subset=["land_type"])

# ---------------------------------
# Reproject everything to meters
# ---------------------------------
gdf = gdf.to_crs(epsg=3857)
roads = roads.to_crs(epsg=3857)

# ---------------------------------
# Convert road lines → polygons (width = 15 m)
# ---------------------------------
roads["geometry"] = roads.geometry.buffer(15)
roads["land_type"] = "road"

# ---------------------------------
# Combine roads with land polygons
# ---------------------------------
gdf = pd.concat([gdf, roads[["geometry", "land_type"]]])

# ---------------------------------
# Compute areas
# ---------------------------------
gdf["area_m2"] = gdf.geometry.area
gdf["area_km2"] = gdf["area_m2"] / 1e6

# ---------------------------------
# Runoff coefficients
# ---------------------------------
C = {
    "road": 0.9,
    "commercial": 0.8,
    "industrial": 0.7,
    "residential": 0.6,
    "park": 0.3,
    "forest": 0.2,
    "water": 0.0
}

gdf["runoff_C"] = gdf["land_type"].map(C)

# ---------------------------------
# Summarize
# ---------------------------------
summary = gdf.groupby("land_type")["area_km2"].sum().reset_index()
summary["runoff_C"] = summary["land_type"].map(C)

summary.to_csv("data/land_use.csv", index=False)

print("\n[SUCCESS] data/land_use.csv created")
print(summary)
