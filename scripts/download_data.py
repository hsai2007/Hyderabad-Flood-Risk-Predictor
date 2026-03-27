import os
import requests
import numpy as np
import json

print("[INFO] Creating data folders...")
os.makedirs("data", exist_ok=True)
os.makedirs("data/dem_tiles", exist_ok=True)
os.makedirs("data/rainfall", exist_ok=True)

# ============================================================
# Download elevation data using Open-Elevation API (no login)
# ============================================================
# Open-Elevation is a free, open-source API that serves SRTM
# elevation data — no NASA account needed.
# We sample a grid of points over Hyderabad and build a
# GeoTIFF raster from them using rasterio.
#
# Hyderabad bounding box:
#   Lat: 17.20 – 17.60
#   Lon: 78.20 – 78.60

print("[INFO] Downloading elevation data from Open-Elevation (no login needed)...")

LAT_MIN, LAT_MAX = 17.20, 17.60
LON_MIN, LON_MAX = 78.20, 78.60

# Grid resolution — 40x40 = 1600 points (fine enough for city-scale)
GRID_N = 40

lats = np.linspace(LAT_MAX, LAT_MIN, GRID_N)  # top to bottom
lons = np.linspace(LON_MIN, LON_MAX, GRID_N)  # left to right

# Build list of all grid points
locations = []
for lat in lats:
    for lon in lons:
        locations.append({"latitude": round(lat, 5), "longitude": round(lon, 5)})

print(f"[INFO] Querying {len(locations)} elevation points...")

# Open-Elevation accepts up to 2000 points per POST request
BATCH_SIZE = 500
elevations = []

for i in range(0, len(locations), BATCH_SIZE):
    batch = locations[i:i+BATCH_SIZE]
    try:
        resp = requests.post(
            "https://api.open-elevation.com/api/v1/lookup",
            json={"locations": batch},
            timeout=60
        )
        results = resp.json()["results"]
        elevations.extend([r["elevation"] for r in results])
        print(f"  [{i + len(batch)}/{len(locations)} points done]")
    except Exception as e:
        print(f"[WARNING] Batch {i} failed: {e} — filling with 0")
        elevations.extend([0] * len(batch))

# ============================================================
# Save as GeoTIFF using rasterio
# ============================================================
import rasterio
from rasterio.transform import from_bounds
from rasterio.crs import CRS

grid = np.array(elevations, dtype=np.float32).reshape(GRID_N, GRID_N)

transform = from_bounds(LON_MIN, LAT_MIN, LON_MAX, LAT_MAX, GRID_N, GRID_N)

out_path = "data/dem_tiles/hyderabad_dem.tif"

with rasterio.open(
    out_path,
    "w",
    driver="GTiff",
    height=GRID_N,
    width=GRID_N,
    count=1,
    dtype=np.float32,
    crs=CRS.from_epsg(4326),
    transform=transform
) as dst:
    dst.write(grid, 1)

print(f"[SUCCESS] Elevation GeoTIFF saved → {out_path}")
print(f"  Elevation range: {grid.min():.0f}m – {grid.max():.0f}m")

# ============================================================
# Also copy directly to data/dem.tif (skips merge_dem.py step)
# ============================================================
import shutil
shutil.copy(out_path, "data/dem.tif")
print("[INFO] Copied to data/dem.tif — you can skip running merge_dem.py")

# ============================================================
# OSM data instructions
# ============================================================
print("""
[MANUAL STEP REQUIRED]

Download Hyderabad OSM GeoJSON from:
https://overpass-turbo.eu

Use this query (paste it in the wizard box):
----------------------------------------------
(
  way["landuse"](17.2,78.2,17.6,78.6);
  way["highway"](17.2,78.2,17.6,78.6);
  way["natural"](17.2,78.2,17.6,78.6);
);
out geom;
----------------------------------------------

Then click Export → GeoJSON and save the file as:
  data/hyderabad_landuse.geojson

Also run a second query for drains and save as data/hyderabad_drains.geojson:
----------------------------------------------
(
  way["waterway"~"drain|stream|canal|river"](17.2,78.2,17.6,78.6);
);
out geom;
----------------------------------------------
""")
