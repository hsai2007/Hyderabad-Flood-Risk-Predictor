import pandas as pd
import networkx as nx

edges = pd.read_csv("data/drain_edges_downhill.csv")
nodes = pd.read_csv("data/node_runoff.csv")

G = nx.DiGraph()

# Build graph
for _, r in edges.iterrows():
    G.add_edge(int(r["from"]), int(r["to"]), length=r["length_m"])

# Initialize node inflow
for _, r in nodes.iterrows():
    G.nodes[int(r["node_id"])]["Q"] = r["runoff_m3s"]

for n in G.nodes:
    if "Q" not in G.nodes[n]:
        G.nodes[n]["Q"] = 0.0

# Topological sort now works (no cycles)
order = list(nx.topological_sort(G))

# Accumulate flows
for u in order:
    for _, v in G.out_edges(u):
        G.nodes[v]["Q"] += G.nodes[u]["Q"]

# Save pipe flows
flows = []
for u, v in G.edges:
    flows.append([u, v, G.nodes[u]["Q"]])

df = pd.DataFrame(flows, columns=["from","to","flow_m3s"])
df.to_csv("data/pipe_flows.csv", index=False)

print("[SUCCESS] Gravity-correct pipe flows computed")
print(df.head())
