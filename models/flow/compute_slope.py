import pandas as pd

edges = pd.read_csv("data/drain_edges_downhill.csv")
nodes = pd.read_csv("data/drain_nodes_with_elevation.csv")

elev = dict(zip(nodes.node_id, nodes.elevation_m))

# ================================
# FIX: Minimum slope raised to engineering standard
# ================================
# Previous code used S_min = 0.0001 (1cm drop per 100m).
# At this slope, Manning's gives near-zero velocity → sewage settles,
# pipes block, and the solver demands impossibly large diameters.
#
# Standard minimum slopes for urban storm drains (IS 1742 / CPHEEO):
#   - Small pipes (< 300mm): S_min = 0.005 (5mm/m)
#   - Medium pipes (300–600mm): S_min = 0.002
#   - Large culverts (> 600mm): S_min = 0.001
#
# We use 0.002 as a general conservative minimum for Hyderabad's
# relatively flat terrain in low-lying areas.

S_MIN = 0.002  # minimum slope = 2mm per metre (engineering standard)

slopes = []
for _, r in edges.iterrows():
    u = int(r["from"])
    v = int(r["to"])
    L = r["length_m"]

    dz = elev[u] - elev[v]

    if L <= 0:
        slopes.append(S_MIN)
        continue

    S = dz / L
    S = max(S, S_MIN)  # enforce minimum
    slopes.append(S)

edges["slope"] = slopes
edges.to_csv("data/drain_edges_with_slope.csv", index=False)

print(f"[SUCCESS] Pipe slopes computed (S_min = {S_MIN})")
print(f"  Slope range: {min(slopes):.4f} – {max(slopes):.4f}")
print(f"  Pipes at minimum slope: {sum(1 for s in slopes if s == S_MIN)}")
