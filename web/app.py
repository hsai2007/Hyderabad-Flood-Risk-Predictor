from flask import Flask, jsonify, send_from_directory
import geopandas as gpd

app = Flask(__name__, static_folder=".")

@app.route("/")
def home():
    return send_from_directory(".", "index.html")

@app.route("/floods")
def floods():
    gdf = gpd.read_file("data/flooded_drains.geojson")
    return gdf.to_json()

if __name__ == "__main__":
    app.run(debug=True)
