import pandas as pd
import networkx as nx

edges = pd.read_csv("data/drain_edges_downhill.csv")
nodes = pd.read_csv("data/node_runoff.csv")

G = nx.DiGraph()

for _, r in edges.iterrows():
    G.add_edge(int(r["from"]), int(r["to"]), length=r["length_m"])

for n in G.nodes:
    G.nodes[n]["Q_local"] = 0.0
    G.nodes[n]["Q_accumulated"] = 0.0

for _, r in nodes.iterrows():
    nid = int(r["node_id"])
    if nid in G.nodes:
        G.nodes[nid]["Q_local"] = r["runoff_m3s"]
        G.nodes[nid]["Q_accumulated"] = r["runoff_m3s"]

# Break cycles before topological sort
# OSM drain data often has cycles from roundabouts or mapping errors.
# We remove the shortest edge in each cycle until the graph is cycle-free.
cycles_removed = 0
while True:
    try:
        cycle = nx.find_cycle(G, orientation="original")
        shortest = min(cycle, key=lambda e: G.edges[e[0], e[1]].get("length", 1))
        G.remove_edge(shortest[0], shortest[1])
        cycles_removed += 1
    except nx.NetworkXNoCycle:
        break

if cycles_removed > 0:
    print(f"[INFO] Removed {cycles_removed} cyclic edges from drain network")

order = list(nx.topological_sort(G))

for u in order:
    out_edges = list(G.out_edges(u))
    if not out_edges:
        continue
    Q_out = G.nodes[u]["Q_accumulated"]
    if len(out_edges) == 1:
        _, v = out_edges[0]
        G.nodes[v]["Q_accumulated"] += Q_out
        G.edges[u, v]["pipe_flow_m3s"] = Q_out
    else:
        lengths = [G.edges[u, v]["length"] for _, v in out_edges]
        inv_lengths = [1.0 / l for l in lengths]
        total_inv = sum(inv_lengths)
        weights = [il / total_inv for il in inv_lengths]
        for (_, v), w in zip(out_edges, weights):
            split_Q = Q_out * w
            G.nodes[v]["Q_accumulated"] += split_Q
            G.edges[u, v]["pipe_flow_m3s"] = split_Q

flows = []
for u, v, data in G.edges(data=True):
    flows.append({"from": u, "to": v, "flow_m3s": data.get("pipe_flow_m3s", 0.0)})

df = pd.DataFrame(flows)
df.to_csv("data/pipe_flows.csv", index=False)
print("[SUCCESS] Pipe flows correctly accumulated")
print(df.head())