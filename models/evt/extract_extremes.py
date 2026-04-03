import pandas as pd
import os

INPUT_FILE = "data/rainfall/hourly_rainfall.csv"
OUTPUT_FILE = "data/rainfall/extreme_events.csv"
MONSOON_MONTHS = [6, 7, 8, 9]

print("[INFO] Loading NASA POWER daily rainfall...")
df = pd.read_csv(INPUT_FILE)
df["date"] = pd.to_datetime(df["date"])
df["month"] = df["date"].dt.month
df["year"] = df["date"].dt.year

df = df[df["month"].isin(MONSOON_MONTHS)]

extremes = df.groupby("year")["rain_mm"].max().reset_index()
extremes.columns = ["year", "rain_24hr"]
extremes["rain_3hr"] = extremes["rain_24hr"] * 0.45
extremes["rain_6hr"] = extremes["rain_24hr"] * 0.64
extremes = extremes.set_index("year")

os.makedirs("data/rainfall", exist_ok=True)
extremes.to_csv(OUTPUT_FILE)

print(f"[SUCCESS] {len(extremes)} years of extreme events extracted")
print(extremes)