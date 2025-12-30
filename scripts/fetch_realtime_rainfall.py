import requests
import pandas as pd

LAT = 17.3850
LON = 78.4867

url = (
    "https://api.open-meteo.com/v1/forecast?"
    f"latitude={LAT}&longitude={LON}"
    "&hourly=precipitation,rain"
    "&forecast_days=7"
    "&timezone=Asia%2FKolkata"
)

r = requests.get(url).json()

df = pd.DataFrame({
    "time": r["hourly"]["time"],
    "rain (mm)": r["hourly"]["rain"]
})

df["time"] = pd.to_datetime(df["time"])

df.to_csv("data/rainfall/realtime_rainfall.csv", index=False)

print(df.head())
