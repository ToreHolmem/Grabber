import requests
import json
import argparse
import os
from rasterio.transform import from_bounds
from rasterio.io import MemoryFile
import numpy as np
from PIL import Image


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

# Create bbox tuple directly from provided coordinates
bbox_tuple = (args.min_x, args.min_y, args.max_x, args.max_y)

# Convert bbox tuple to a string for the request URL
bbox = ','.join(map(str, bbox_tuple))

print("Bounding box:", bbox)

# Construct the query URL for the Export Map operation
export_url = 'https://services.geodataonline.no/arcgis/rest/services/Geomap_UTM33_EUREF89/GeomapArealressurs/MapServer/export'

# Specify the parameters for the request
#     'layers': 'show:70,40,6,19,20,21,23,24,25,26,27,
params = {
    'f': 'image',
    'format': 'png',
    'bbox': bbox,
    'size': '4096,4096',
    'bboxSR': '25833',
    'imageSR': '25833',
    'layers': 'show:70,',
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
    print("Map exported as PNG and saved to:", args.final_output_path)
else:
    print("Failed to retrieve data. Status code:", response.status_code)
    print("Response content:", response.text)

# print("URL:", response.url)
# print("Bounding Box:", params['bbox'])
# print("Layers:", params['layers'])
# print("Format:", params['format'])
# print("Spatial Reference (bboxSR and imageSR):", params['bboxSR'])
# print("Token Used:", params['token'])

print("Export Map operation completed.")

# Define the paths for the PNG and GeoTIFF files
png_path = args.final_output_path
geotiff_path = os.path.join(os.path.dirname(args.final_output_path), 'output.tif')



def convert_png_to_geotiff(png_path, geotiff_path, bbox, crs='EPSG:25833'):
    # Open the PNG image with PIL and convert to numpy array
    with Image.open(png_path) as img:
        data = np.array(img)

    # Ensure data is in 3 bands (RGB), drop the alpha channel if present
    if len(data.shape) == 3 and data.shape[2] > 3:
        data = data[:, :, :3]

    # Calculate the transformation using the bounding box
    transform = from_bounds(*bbox, data.shape[1], data.shape[0])

    # Define the metadata for the new GeoTIFF
    metadata = {
        'driver': 'GTiff',
        'dtype': 'uint8',
        'count': 3,
        'height': data.shape[0],
        'width': data.shape[1],
        'transform': transform,
        'crs': crs
    }

    print("Converting PNG to GeoTIFF...")

    # Call the function to convert PNG to GeoTIFF
    convert_png_to_geotiff(png_path, geotiff_path, bbox)

    # Write the data to a new GeoTIFF file
    with MemoryFile() as memfile:
        with memfile.open(**metadata) as dst:
            for i in range(1, 4):  # Write each band
                dst.write(data[:, :, i-1], i)
        
        # Save the GeoTIFF to the filesystem
        with open(geotiff_path, 'wb') as f:
            f.write(memfile.read())

    print("GeoTIFF saved to:", geotiff_path)
