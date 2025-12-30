import pandas as pd

flood = pd.read_csv("data/flood_risk.csv")

# Sort by highest clogging & flooding
worst = flood.sort_values(
    by=["P_clog","flow_m3s"],
    ascending=False
)

print("\n[TOP 20 FLOOD-PRONE DRAINS]")
print(worst.head(20))

worst.head(20).to_csv("data/top_flood_risk.csv", index=False)
