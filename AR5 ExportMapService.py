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
file_name = "map.svg"
output_path = os.path.join(output_directory, file_name)

# Load the token from token.json
with open('token.json', 'r') as file:
    token_data = json.load(file)
token = token_data['token']

# Directly use EPSG codes for defining source and destination CRS for the transformation
transformer = Transformer.from_crs("EPSG:4326", "EPSG:25833", always_xy=True)

# Provided coordinates
lat, lon = args.center_lat, args.center_lon

# Convert coordinates to UTM33N using the transformer
# Note: Transformer uses lon, lat order for input when always_xy=True
x, y = transformer.transform(lon, lat)

# Define the size of the square in meters
size = 1000  # 1 km on each side for a total square of 2x2 km

# Define the 2 km square bounds around the coordinate
extent = [x - size / 2, y - size / 2, x + size / 2, y + size / 2]
bbox = ','.join(map(str, extent))

# Construct the query URL for the Export Map operation
export_url = 'https://services.geodataonline.no/arcgis/rest/services/Geomap_UTM33_EUREF89/GeomapArealressurs/MapServer/export'

# Specify the parameters for the request
params = {
    'f': 'image',
    'format': 'svg',
    'bbox': bbox,
    'size': '1024,1024',
    'bboxSR': '25833',
    'imageSR': '25833',
    'layers': 'show:19,20,21,22,23,24,25,26,27,28,29',  # Example layers, adjust as needed
    'token': token,
    'transparent': 'true',
    # Include any other parameters you might need
}

# Perform the GET request with the token included
response = requests.get(export_url, params=params)

# Check if the request was successful
if response.status_code == 200:
    # Save the SVG data to a file
    with open(output_path, 'wb') as file:
        file.write(response.content)
    print("Map exported as SVG and saved to:", output_path)
else:
    print("Failed to retrieve data. Status code:", response.status_code)
    print("Response content:", response.text)
