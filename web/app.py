from flask import Flask, jsonify, send_from_directory
import geopandas as gpd
import pandas as pd
import json

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
        drains = gpd.read_file("data/hyderabad_drains.geojson")
        risk   = pd.read_csv("data/flood_risk.csv")

        drains = drains.reset_index().rename(columns={"index": "edge_id"})
        risk["edge_id"] = risk.index
        merged = drains.merge(risk, on="edge_id", how="left")

        def risk_color(row):
            if row.get("flooding") == True:
                return "red"
            p = row.get("P_clog", 0)
            if pd.isna(p):
                return "blue"
            if p > 0.5:
                return "orange"
            if p > 0.2:
                return "yellow"
            return "green"

        merged["risk_color"] = merged.apply(risk_color, axis=1)
        merged["P_clog"]     = merged["P_clog"].fillna(0).round(3)
        merged["flooding"]   = merged["flooding"].fillna(False)
        merged["flow_m3s"]   = merged["flow_m3s"].fillna(0).round(3)

        return merged.to_json()
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route("/risk_points")
def risk_points():
    try:
        risk  = pd.read_csv("data/flood_risk.csv")
        nodes = pd.read_csv("data/drain_nodes_with_elevation.csv")

        node_coords = nodes.set_index("node_id")[["x","y","elevation_m"]]
        risk = risk.merge(node_coords, left_on="from", right_index=True, how="left")

        import geopandas as gpd
        from shapely.geometry import Point
        gdf = gpd.GeoDataFrame(
            risk,
            geometry=gpd.points_from_xy(risk["x"], risk["y"]),
            crs="EPSG:3857"
        ).to_crs("EPSG:4326")

        gdf["lat"] = gdf.geometry.y
        gdf["lon"] = gdf.geometry.x

        top = gdf.sort_values("P_clog", ascending=False).head(20)
        result = top[["from","to","flow_m3s","P_clog","flooding","lat","lon"]].to_dict(orient="records")
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == "__main__":
    app.run(debug=True)