import geopandas as gpd
import pandas as pd
import shapely.geometry as geom

# Load drains
gdf = gpd.read_file("data/hyderabad_drains.geojson")

# Keep only lines
gdf = gdf[gdf.geometry.type.isin(["LineString","MultiLineString"])]

gdf = gdf.to_crs(epsg=3857)  # meters

nodes = {}
edges = []

node_id = 0

def get_node(pt):
    global node_id
    key = (round(pt.x,1), round(pt.y,1))
    if key not in nodes:
        nodes[key] = node_id
        node_id += 1
    return nodes[key]

for _, row in gdf.iterrows():
    geom_line = row.geometry
    if geom_line.geom_type == "MultiLineString":
        lines = geom_line.geoms
    else:
        lines = [geom_line]

    for line in lines:
        start = geom.Point(line.coords[0])
        end   = geom.Point(line.coords[-1])

        u = get_node(start)
        v = get_node(end)

        length = line.length

        edges.append((u, v, length))

# Save graph
nodes_df = pd.DataFrame(
    [(k[0], k[1], v) for k,v in nodes.items()],
    columns=["x","y","node_id"]
)

edges_df = pd.DataFrame(edges, columns=["from","to","length_m"])

nodes_df.to_csv("data/drain_nodes.csv", index=False)
edges_df.to_csv("data/drain_edges.csv", index=False)

print("[SUCCESS] Drainage graph created")
print("Nodes:", len(nodes_df))
print("Edges:", len(edges_df))
