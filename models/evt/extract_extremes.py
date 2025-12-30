import pandas as pd
import os

# ================================
# Configuration
# ================================
INPUT_FILE = "data/rainfall/hourly_rainfall.csv"
OUTPUT_FILE = "data/rainfall/extreme_events.csv"

# India monsoon months
MONSOON_MONTHS = [6, 7, 8, 9]

# Rolling window sizes (hours)
WINDOWS = {
    "3hr": 3,
    "6hr": 6
}

# ================================
# Load rainfall data
# ================================
print("[INFO] Loading hourly rainfall data...")

df = pd.read_csv(INPUT_FILE, encoding="utf-8-sig")
df.columns = df.columns.str.strip()   # remove invisible spaces
print("Columns found:", list(df.columns))


# Convert time column
time_col = None
for col in df.columns:
    if "time" in col.lower():
        time_col = col
        break

if time_col is None:
    raise Exception("No time column found. Columns are: " + str(df.columns))

df["time"] = pd.to_datetime(df[time_col])


# Choose correct rainfall column
# -------------------------------
# Select rainfall column
# -------------------------------
if "rain (mm)" in df.columns:
    df["rain_mm"] = df["rain (mm)"]
    print("[INFO] Using 'rain (mm)' column")
elif "precipitation (mm)" in df.columns:
    df["rain_mm"] = df["precipitation (mm)"]
    print("[INFO] Using 'precipitation (mm)' column")
else:
    raise Exception("No rainfall column found! Found columns: " + str(df.columns))

df = df[["time", "rain_mm"]]
df = df.dropna()

# ================================
# Filter only monsoon months
# ================================
print("[INFO] Filtering monsoon months (June–September)...")

df["month"] = df["time"].dt.month
df = df[df["month"].isin(MONSOON_MONTHS)]

# ================================
# Sort by time
# ================================
df = df.sort_values("time")

# ================================
# Compute rolling storm rainfall
# ================================
print("[INFO] Computing rolling storm rainfall...")

for label, hours in WINDOWS.items():
    df[f"rain_{label}"] = df["rain_mm"].rolling(hours).sum()

# ================================
# Extract yearly maximum storms
# ================================
print("[INFO] Extracting yearly extreme events...")

df["year"] = df["time"].dt.year

extremes = df.groupby("year")[[f"rain_{k}" for k in WINDOWS.keys()]].max()

# ================================
# Save to CSV
# ================================
os.makedirs("data/rainfall", exist_ok=True)
extremes.to_csv(OUTPUT_FILE)

print("\n[SUCCESS] Extreme rainfall events saved to:")
print(OUTPUT_FILE)
print("\nSample:")
print(extremes.head())
