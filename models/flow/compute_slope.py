import pandas as pd

edges = pd.read_csv("data/drain_edges_downhill.csv")
nodes = pd.read_csv("data/drain_nodes_with_elevation.csv")

elev = dict(zip(nodes.node_id, nodes.elevation_m))

slopes = []
for _, r in edges.iterrows():
    u = int(r["from"])
    v = int(r["to"])
    L = r["length_m"]

    dz = elev[u] - elev[v]
    S = max(dz / L, 0.0001)   # prevent zero slope
    slopes.append(S)

edges["slope"] = slopes
edges.to_csv("data/drain_edges_with_slope.csv", index=False)

print("[SUCCESS] Pipe slopes computed")
