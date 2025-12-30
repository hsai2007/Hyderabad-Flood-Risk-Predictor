import pandas as pd

edges = pd.read_csv("data/drain_edges.csv")
nodes = pd.read_csv("data/drain_nodes_with_elevation.csv")

elev = dict(zip(nodes.node_id, nodes.elevation_m))

new_edges = []

for _, r in edges.iterrows():
    u = int(r["from"])
    v = int(r["to"])

    # Force flow downhill
    if elev[u] >= elev[v]:
        new_edges.append([u, v, r["length_m"]])
    else:
        new_edges.append([v, u, r["length_m"]])

df = pd.DataFrame(new_edges, columns=["from","to","length_m"])
df.to_csv("data/drain_edges_downhill.csv", index=False)

print("[SUCCESS] Drainage network oriented by gravity")
