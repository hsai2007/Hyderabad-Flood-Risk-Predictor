import requests
import pandas as pd
import os

url = "https://power.larc.nasa.gov/api/temporal/daily/point"

params = {
    "parameters": "PRECTOTCORR",
    "community": "RE",
    "longitude": 78.4744,
    "latitude": 17.3850,
    "start": "19900101",
    "end": "20241231",
    "format": "JSON"
}

print("[INFO] Fetching NASA POWER rainfall data (1990–2024)...")
response = requests.get(url, params=params)
data = response.json()

daily = data["properties"]["parameter"]["PRECTOTCORR"]
df = pd.DataFrame(list(daily.items()), columns=["date", "rain_mm"])
df["date"] = pd.to_datetime(df["date"], format="%Y%m%d")
df = df[df["rain_mm"] >= 0]

os.makedirs("data/rainfall", exist_ok=True)
df.to_csv("data/rainfall/hourly_rainfall.csv", index=False)
print(f"[SUCCESS] {len(df)} days of rainfall data saved")
print(df.tail())