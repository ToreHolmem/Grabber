from pyproj import Transformer
import requests
import json
import argparse
import os

# part 0: parse arguments
parser = argparse.ArgumentParser()
parser.add_argument("center_lat", type=float)
parser.add_argument("center_lon", type=float)
parser.add_argument("output_location", type=str)
args = parser.parse_args()

output_directory = args.output_location
combined_file_name = "Combined_FKB.geojson"
output_path = os.path.join(output_directory, combined_file_name)

# Load the token from token.json
with open('token.json', 'r') as file:
    token_data = json.load(file)
token = token_data['token']

# Directly use EPSG codes for defining source and destination CRS for the transformation
transformer = Transformer.from_crs("EPSG:4326", "EPSG:25833", always_xy=True)

# Provided coordinates
lat, lon = args.center_lat, args.center_lon

# Convert coordinates to UTM33N
x, y = transformer.transform(lon, lat)

# Define the size of the square in meters
size = 1000  # 1 km square for simplicity

# Define the square bounds around the coordinate
extent = [x - size, y - size, x + size, y + size]

# List of layers to be fetched
# 51 - Treslag
# 52 - Bonitet
# 19 - Fulldyrka jord
# 20 - Overflatedyrka jord
# 21 - Innmarksbeite
# 22 - Skog
# 23 - Myr
# 24 - Åpen Fastmark
# 25 - Ferskvann
# 26 - Hav
# 27 - Bre
# 28 - Bebygd
# 29 - Samferdsel
# 51, 52, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29
layer_ids = [22]

# Initialize an empty GeoJSON structure
combined_geojson = {
    "type": "FeatureCollection",
    "features": []
}

# Iterate over each layer ID to fetch and combine data
for layer_id in layer_ids:
    # Construct the query URL for the current layer
    url = f"https://services.geodataonline.no/arcgis/rest/services/Geomap_UTM33_EUREF89/GeomapArealressurs/MapServer/{layer_id}/query"

    geometry = {
        'xmin': extent[0],
        'ymin': extent[1],
        'xmax': extent[2],
        'ymax': extent[3],
        'spatialReference': {"wkid": 25833}
    }

    params = {
        'f': 'geojson',
        'returnGeometry': 'true',
        'spatialRel': 'esriSpatialRelIntersects',
        'geometry': json.dumps(geometry),
        'geometryType': 'esriGeometryEnvelope',
        'inSR': '25833',
        'outFields': '*',
        'outSR': '25833',
        'token': token
    }

    response = requests.get(url, params=params)

    if response.status_code == 200:
        layer_data = response.json()
        if 'error' not in layer_data:
            # Append features from the current layer to the combined GeoJSON
            combined_geojson['features'].extend(layer_data['features'])
        else:
            print(f"Error returned from server for layer {layer_id}:", layer_data['error'])
    else:
        print(f"Failed to retrieve data for layer {layer_id}. Status code:", response.status_code)
        print("Response content:", response.text)

# Save the combined GeoJSON data to a file
with open(output_path, 'w') as f:
    json.dump(combined_geojson, f)
print("Combined GeoJSON data retrieved and saved.")
