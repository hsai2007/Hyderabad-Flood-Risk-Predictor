import requests
import pandas as pd

LAT = 17.3850
LON = 78.4867

url = (
    "https://archive-api.open-meteo.com/v1/archive?"
    f"latitude={LAT}&longitude={LON}"
    "&start_date=2010-01-01"
    "&end_date=2024-12-31"
    "&hourly=rain"
    "&timezone=Asia%2FKolkata"
)

r = requests.get(url).json()

df = pd.DataFrame({
    "time": r["hourly"]["time"],
    "rain (mm)": r["hourly"]["rain"]
})

df["time"] = pd.to_datetime(df["time"])
df = df.dropna()

df.to_csv("data/rainfall/hourly_rainfall.csv", index=False)

print("[SUCCESS] Historical rainfall downloaded")
print(df.head())
