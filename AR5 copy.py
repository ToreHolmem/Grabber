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
file_name = "FKB.geojson"
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
size = 1000  # 4 km

# Define the 4 km square bounds around the coordinate
extent = [x - size, y - size, x + size, y + size]

# Interessante datalag: 
# Treslag (51) - Virker tettere enn det jeg har hatt tidligere.
# Bonitet (52) - Kan kanskje krysses for å sikre tetthet.
# Fulldyrka jord (19)
# Overflatedyrka jord (20)
# Innmarksbeite (21)
# Skog (22)
# Myr (23)
# Åpen fastmark (24)
# Ferskvann (25)
# Hav (26)
# Bre (27)
# Bebygd (28)
# Samferdsel (29)

layer_id = 3

# Construct the query URL
url = f"https://services.geodataonline.no/arcgis/rest/services/Geomap_UTM33_EUREF89/GeomapArealressurs/MapServer/{layer_id}/query"

# Update parameters to include the token
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
    'geometry': json.dumps(geometry),  # Convert the geometry object to a JSON string
    'geometryType': 'esriGeometryEnvelope',
    'inSR': '25833',
    'outFields': '*',
    'outSR': '25833',
    'token': token
}

# Perform the GET request with the token included
response = requests.get(url, params=params)

# Check if the request was successful
if response.status_code == 200:
    data = response.json()  # This is your GeoJSON data
    # Check if there is an error field in the JSON response
    if 'error' in data:
        print("Error returned from server:", data['error'])
    else:
        # Save this data to a file
        with open(output_path, 'w') as f:
            json.dump(data, f)
        print("Data retrieved and saved.")
else:
    print("Failed to retrieve data. Status code:", response.status_code)
    print("Response content:", response.text)