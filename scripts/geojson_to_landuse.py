import geopandas as gpd
import pandas as pd

# Load GeoJSON
gdf = gpd.read_file("data/hyderabad_landuse.geojson")

print("[INFO] Columns found:", gdf.columns.tolist())

# ---------------------------------
# Separate roads (LINE features)
# ---------------------------------
roads = gdf[gdf["highway"].notna()].copy()
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
# Reproject everything to metres
# ---------------------------------
gdf   = gdf.to_crs(epsg=3857)
roads = roads.to_crs(epsg=3857)

# ---------------------------------
# FIX: Road width by highway type (not a flat 15m for everything)
# ---------------------------------
# OSM highway tag → typical carriageway half-width (buffer in metres)
# Sources: IRC:86 (Indian Road Congress geometric design standards)
ROAD_WIDTHS = {
    "motorway":      30,   # 6-lane expressway
    "trunk":         20,   # 4-lane arterial
    "primary":       15,   # 4-lane primary road
    "secondary":     10,   # 2-lane secondary road
    "tertiary":       7,   # 2-lane local road
    "residential":    5,   # residential street
    "service":        4,   # service lane / access road
    "footway":        2,   # pedestrian path
    "path":           1.5,
    "cycleway":       2,
    "unclassified":   6,   # default for unknown
}

def road_buffer(highway_type):
    return ROAD_WIDTHS.get(str(highway_type).lower(), 6)  # default 6m

roads["buffer_m"] = roads["highway"].apply(road_buffer)
roads["geometry"] = roads.apply(lambda r: r.geometry.buffer(r["buffer_m"]), axis=1)
roads["land_type"] = "road"

# ---------------------------------
# Combine roads with land polygons
# ---------------------------------
gdf = pd.concat([gdf, roads[["geometry", "land_type"]]])

# ---------------------------------
# Compute areas
# ---------------------------------
gdf["area_m2"]  = gdf.geometry.area
gdf["area_km2"] = gdf["area_m2"] / 1e6

# ---------------------------------
# FIX: Runoff coefficients — water bodies get C=0.1 not 0.0
# ---------------------------------
# Water bodies (lakes, tanks) in Hyderabad (Hussain Sagar, Durgam Cheruvu etc.)
# can overflow when rainfall exceeds their capacity. Using C=0.0 completely
# ignores this common flood mechanism. C=0.1 is a conservative estimate
# representing overflow contribution during extreme events.
C = {
    "road":        0.9,
    "commercial":  0.8,
    "industrial":  0.7,
    "residential": 0.6,
    "park":        0.3,
    "forest":      0.2,
    "water":       0.1   # FIX: was 0.0 — now accounts for overflow risk
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
