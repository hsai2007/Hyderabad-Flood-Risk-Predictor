# Hyderabad-Risk-Flood-Predictor
EVT-based(Probability Model) urban flood risk prediction system for Hyderabad using rainfall, land use, drainage networks, and GIS.

## How to Reproduce the Model

### 1. Download base data
Run:
python scripts/download_data.py

Download Hyderabad GeoJSON from Overpass Turbo and save to:

data/hyderabad_landuse.geojson

### 2. Build GIS layers
Run:
python scripts/geojson_to_landuse.py

python models/flow/catchment_mapper.py

python models/flow/sample_elevation.py

python models/flow/orient_by_slope.py

### 3. Run the full flood model
Run:
python run_flood_model.py

python web/app.py

### 4. Open:
http://127.0.0.1:5000

## Live Flood Map

![Map](screenshots/map.png)

![Floods](screenshots/floods.png)

