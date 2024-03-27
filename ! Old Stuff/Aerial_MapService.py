import requests
import json
import argparse
import os

# Updated argparse to match the requirements for direct bounding box use and final output path
parser = argparse.ArgumentParser(description="Export a map image for a specific bounding box.")
parser.add_argument("min_x", type=float, help="Minimum X coordinate of the bounding box.")
parser.add_argument("min_y", type=float, help="Minimum Y coordinate of the bounding box.")
parser.add_argument("max_x", type=float, help="Maximum X coordinate of the bounding box.")
parser.add_argument("max_y", type=float, help="Maximum Y coordinate of the bounding box.")
parser.add_argument("temp_dir", type=str, help="Temporary directory path for storing intermediate files, not used in this script.")
parser.add_argument("final_output_path", type=str, help="Path to save the final map image.")
args = parser.parse_args()

# Load the token from token.json
with open('token.json', 'r') as file:
    token_data = json.load(file)
token = token_data['token']

# Directly use the provided bounding box for the export
bbox = ','.join(map(str, [args.min_x, args.min_y, args.max_x, args.max_y]))

print("Bounding box:", bbox)

# Construct the query URL for the Export Map operation
export_url = 'https://services.geodataonline.no/arcgis/rest/services/Geocache_UTM33_WGS84/GeocacheBilder/MapServer/export'

# Specify the parameters for the request
params = {
    'f': 'image',
    'format': 'png',
    'bbox': bbox,
    'size': '2048,2048',
    # 'bboxSR': '25833',
    # 'imageSR': '25833',
    # 'layers': '0',
    'token': token,
    'transparent': 'false',
}

# Perform the GET request with the specified parameters
response = requests.get(export_url, params=params)

# Check if the request was successful
if response.status_code == 200:
    # Save the response content to the final output path
    with open(args.final_output_path, 'wb') as file:
        file.write(response.content)
    print("Map exported as SVG and saved to:", args.final_output_path)
else:
    print("Failed to retrieve data. Status code:", response.status_code)
    print("Response content:", response.text)

print("URL:", response.url)
print("Bounding Box:", params['bbox'])
# print("Layers:", params['layers'])
# print("Format:", params['format'])
# print("Spatial Reference (bboxSR and imageSR):", params['bboxSR'])
# print("Token Used:", params['token'])
