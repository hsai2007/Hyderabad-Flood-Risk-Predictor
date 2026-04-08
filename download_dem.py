import requests
import os
import sys

url = "https://portal.opentopography.org/API/globaldem"

params = {
    "demtype":      "SRTMGL1",
    "south":        17.10,
    "north":        17.70,
    "west":         78.10,
    "east":         78.70,
    "outputFormat": "GTiff",
    "API_Key":      "demoapikeyot2022"
}

print("[INFO] Downloading SRTM 30m DEM for Hyderabad...")
print("  Area: 78.1E-78.7E, 17.1N-17.7N")
print("  Expected: ~2000 x 2000 pixels at 30m resolution")
print("  Please wait — file is roughly 15-20 MB...")

try:
    response = requests.get(
        url,
        params=params,
        stream=True,
        timeout=180
    )

    if response.status_code == 200:
        output_path = "data/dem.tif"
        total_bytes = 0

        with open(output_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
                total_bytes += len(chunk)
                mb = total_bytes / 1024 / 1024
                print(f"\r  Downloaded: {mb:.1f} MB", end="")
                sys.stdout.flush()

        print()
        print(f"[SUCCESS] Saved to {output_path}")
        print(f"  Total size: {total_bytes/1024/1024:.1f} MB")

        # Verify immediately
        import rasterio
        with rasterio.open(output_path) as src:
            import numpy as np
            data = src.read(1)
            valid = data[data > 0]
            print(f"\n[VERIFY] DEM quality check:")
            print(f"  Size:       {src.width} x {src.height} pixels")
            print(f"  Resolution: {round(src.res[0]*111000, 1)}m per pixel")
            print(f"  Coverage:   {src.bounds}")
            print(f"  Elevation:  {valid.min():.0f}m to {valid.max():.0f}m")

            if src.width < 500:
                print("\n[WARNING] DEM is still too small — API key may be invalid")
                print("  Try Option 2: https://bhuvan.nrsc.gov.in")
            else:
                print("\n[GOOD] DEM looks correct — ready to rerun pipeline")

    else:
        print(f"\n[ERROR] Download failed: HTTP {response.status_code}")
        print(response.text[:300])
        print("\nTry manually at: https://portal.opentopography.org")

except requests.exceptions.Timeout:
    print("\n[ERROR] Request timed out — server took too long")
    print("Try again or use: https://bhuvan.nrsc.gov.in")

except Exception as e:
    print(f"\n[ERROR] {e}")