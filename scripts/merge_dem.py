import rasterio
from rasterio.merge import merge
import glob

files = glob.glob("data/dem_tiles/*.tif")

rasters = [rasterio.open(f) for f in files]

mosaic, transform = merge(rasters)

meta = rasters[0].meta.copy()
meta.update({
    "height": mosaic.shape[1],
    "width": mosaic.shape[2],
    "transform": transform
})

with rasterio.open("data/dem.tif", "w", **meta) as dest:
    dest.write(mosaic)

print("[SUCCESS] DEM merged → data/dem.tif")
