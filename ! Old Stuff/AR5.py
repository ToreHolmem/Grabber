import requests
import json
import argparse
import os

# Updated argparse to include min_x, min_y, max_x, max_y, temp_dir, and final_output_path
parser = argparse.ArgumentParser(description="Export a combined GeoJSON for a specific bounding box.")
parser.add_argument("min_x", type=float, help="Minimum X coordinate of the bounding box.")
parser.add_argument("min_y", type=float, help="Minimum Y coordinate of the bounding box.")
parser.add_argument("max_x", type=float, help="Maximum X coordinate of the bounding box.")
parser.add_argument("max_y", type=float, help="Maximum Y coordinate of the bounding box.")
parser.add_argument("temp_dir", type=str, help="Temporary directory path for storing intermediate files, not used in this script.")
parser.add_argument("final_output_path", type=str, help="Path to save the final GeoJSON data.")
args = parser.parse_args()

# Load the token from token.json
with open('token.json', 'r') as file:
    token_data = json.load(file)
token = token_data['token']

# List of layers to be fetched
layer_ids = [22]  # Example layer, adjust as needed

# Initialize an empty GeoJSON structure
combined_geojson = {
    "type": "FeatureCollection",
    "features": []
}

# Iterate over each layer ID to fetch and combine data
for layer_id in layer_ids:
    url = f"https://services.geodataonline.no/arcgis/rest/services/Geomap_UTM33_EUREF89/GeomapArealressurs/MapServer/{layer_id}/query"

    geometry = {
        'xmin': args.min_x,
        'ymin': args.min_y,
        'xmax': args.max_x,
        'ymax': args.max_y,
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
            combined_geojson['features'].extend(layer_data['features'])
        else:
            print(f"Error returned from server for layer {layer_id}:", layer_data['error'])
    else:
        print(f"Failed to retrieve data for layer {layer_id}. Status code:", response.status_code)
        print("Response content:", response.text)

# Save the combined GeoJSON data to the specified final output path
with open(args.final_output_path, 'w') as f:
    json.dump(combined_geojson, f)
print("Combined GeoJSON data retrieved and saved to:", args.final_output_path)
