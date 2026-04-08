from flask import Flask, jsonify, send_from_directory
import geopandas as gpd
import pandas as pd

app = Flask(__name__, static_folder=".")

@app.route("/")
def home():
    return send_from_directory(".", "index.html")

@app.route("/floods")
def floods():
    try:
        gdf = gpd.read_file("data/flooded_drains.geojson")
        return gdf.to_json()
    except Exception as e:
        return jsonify({"type": "FeatureCollection", "features": []})

@app.route("/all_pipes")
def all_pipes():
    try:
        gdf = gpd.read_file("data/drain_risk.geojson")
        return gdf.to_json()
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route("/risk_points")
def risk_points():
    try:
        risk = pd.read_csv("data/flood_risk.csv")

        # Only urban drains — exclude rivers and zero flow
        risk = risk[(risk["flow_m3s"] > 0) & (risk["is_river"] == False)].copy()

        nodes = pd.read_csv("data/drain_nodes_with_elevation.csv")
        node_coords = nodes.set_index("node_id")[["x", "y", "elevation_m"]]

        risk = risk.merge(node_coords, left_on="from", right_index=True, how="left")
        risk = risk.dropna(subset=["x", "y"])

        gdf = gpd.GeoDataFrame(
            risk,
            geometry=gpd.points_from_xy(risk["x"], risk["y"]),
            crs="EPSG:3857"
        ).to_crs("EPSG:4326")

        gdf["lat"] = gdf.geometry.y
        gdf["lon"] = gdf.geometry.x

        top = gdf.sort_values(
            ["flooding", "overflow_m3s"],
            ascending=[False, False]
        ).head(20)

        result = top[[
            "from", "to",
            "flow_m3s", "overflow_m3s",
            "P_clog", "flooding",
            "lat", "lon"
        ]].to_dict(orient="records")

        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == "__main__":
    app.run(debug=True)