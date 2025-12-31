import os
import requests
import zipfile
import io

print("[INFO] Creating data folders...")
os.makedirs("data", exist_ok=True)
os.makedirs("data/dem_tiles", exist_ok=True)

# ----------------------------
# Download SRTM DEM tiles
# ----------------------------
print("[INFO] Downloading SRTM DEM tiles...")

urls = [
    "https://e4ftl01.cr.usgs.gov/MEASURES/SRTMGL1.003/2000.02.11/N17E078.SRTMGL1.hgt.zip"
]

for url in urls:
    name = url.split("/")[-1]
    print("Downloading", name)
    r = requests.get(url)
    z = zipfile.ZipFile(io.BytesIO(r.content))
    z.extractall("data/dem_tiles")

print("[SUCCESS] DEM tiles downloaded")

# ----------------------------
# OSM data instructions
# ----------------------------
print("""
[MANUAL STEP REQUIRED]

Download Hyderabad OSM GeoJSON from:
https://overpass-turbo.eu

Query:
(
  way["landuse"](17.2,78.2,17.6,78.6);
  way["highway"](17.2,78.2,17.6,78.6);
  way["natural"](17.2,78.2,17.6,78.6);
);
out geom;

Export as GeoJSON and save as:
data/hyderabad_landuse.geojson

""")
