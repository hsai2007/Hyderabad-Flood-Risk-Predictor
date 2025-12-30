import rasterio
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point

# Load drain nodes
nodes = pd.read_csv("data/drain_nodes.csv")

# Convert to GeoDataFrame (current CRS is EPSG:3857)
gdf = gpd.GeoDataFrame(
    nodes,
    geometry=gpd.points_from_xy(nodes.x, nodes.y),
    crs="EPSG:3857"
)

# Open DEM
with rasterio.open("data/dem.tif") as dem:
    dem_crs = dem.crs

    # Reproject drain nodes to DEM CRS (usually EPSG:4326)
    gdf = gdf.to_crs(dem_crs)

    # Extract coordinates
    coords = [(pt.x, pt.y) for pt in gdf.geometry]

    # Sample elevation
    elev = [v[0] for v in dem.sample(coords)]

gdf["elevation_m"] = elev

# Save back
out = pd.DataFrame({
    "node_id": gdf["node_id"],
    "x": nodes["x"],
    "y": nodes["y"],
    "elevation_m": elev
})

out.to_csv("data/drain_nodes_with_elevation.csv", index=False)

print("[SUCCESS] Elevation sampled for all drain nodes")
print(out.head())
