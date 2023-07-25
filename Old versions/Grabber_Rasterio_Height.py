# Import the necessary libraries
import numpy as np
import requests
import os
import glob
from PIL import Image
from io import BytesIO
import pyproj
import rasterio
from rasterio.transform import from_origin
from math import cos, pi
from tqdm import tqdm


# Create the output directory if it doesn't exist
output_dir = "../Output"
print(f"Creating output directory {output_dir} if it doesn't exist...")
os.makedirs(output_dir, exist_ok=True)
print(f"Output directory {output_dir} created or already exists.")

# Find the highest existing filename
print("Finding the highest existing filename...")
files = glob.glob(os.path.join(output_dir, "height_*.tif"))
files = [file for file in files if "height_normalized_" not in file]
if not files:
    # No files, start from 0001
    print("No previous files found. Starting from 0001.")
    next_file_number = 1
else:
    # Get the file number part of the filename, convert to int and get the max
    file_numbers = [
        int(os.path.splitext(os.path.basename(file))[0].split('_')[1])
        for file in files
        if len(os.path.splitext(os.path.basename(file))[0].split('_')) == 2
    ]
    next_file_number = max(file_numbers) + 1
    print(f"Previous files found. Continuing from {next_file_number:04d}.")

# Create the output filename with the next file number
output_filename = os.path.join(output_dir, "height_{:04d}.tif".format(next_file_number))
print(f"Output filename set as {output_filename}")

# Helper functions
def download_tile(bbox, width, height):
    base_url = "https://services.geodataonline.no/arcgis/rest/services/Geocache_UTM33_EUREF89/GeocacheTerreng/ImageServer"
    bbox_str = ','.join(map(str, bbox))

    # Request parameters
    params = {
        'bbox': bbox_str,
        'imageSR': 25833,
        'bboxSR': 25833,
        'size': f'{width},{height}',
        'format': 'tiff',
        'pixelType': 'F32',
        'f': 'image'
    }

    # Send the request
    try:
        response = requests.get(base_url + "/exportImage", params=params)
        response.raise_for_status()  # Raise an exception if the response indicates an error
    except requests.exceptions.HTTPError as errh:
        print(f"HTTP Error: {errh}")
        return None
    except requests.exceptions.ConnectionError as errc:
        print(f"Error Connecting: {errc}")
        return None
    except requests.exceptions.Timeout as errt:
        print(f"Timeout Error: {errt}")
        return None
    except requests.exceptions.RequestException as err:
        print(f"Something went wrong: {err}")
        return None

    return Image.open(BytesIO(response.content))


def transform_bbox(bbox, src_crs, dst_crs):
    transformer = pyproj.Transformer.from_crs(src_crs, dst_crs, always_xy=True)
    min_x, min_y = transformer.transform(bbox[0], bbox[1])
    max_x, max_y = transformer.transform(bbox[2], bbox[3])
    return (min_x, min_y, max_x, max_y)

# Parameters
center_lat = 62.45420359364632
center_lon = 7.668951948534192
half_size = 0.5 * 1000 / 2  # Set size

# Calculate bounding box
min_x = center_lon - half_size / (111.32 * 1000 * cos(center_lat * pi / 180))
max_x = center_lon + half_size / (111.32 * 1000 * cos(center_lat * pi / 180))
min_y = center_lat - half_size / (111.32 * 1000)
max_y = center_lat + half_size / (111.32 * 1000)

bbox = (min_x, min_y, max_x, max_y)
bbox_utm = transform_bbox(bbox, "epsg:4326", "epsg:32633")

zoom_level = 18  # Set your desired zoom level (e.g., 18 for max resolution)
resolution_base = 0.1  # meters per pixel at zoom level 18
resolution = resolution_base * (2**(18 - zoom_level))  # Calculate resolution for the desired zoom level

tile_size = 256  # number of pixels per tile

delta_x = resolution * tile_size
delta_y = resolution * tile_size

num_tiles_x = int((bbox_utm[2] - bbox_utm[0]) / delta_x) + 1
num_tiles_y = int((bbox_utm[3] - bbox_utm[1]) / delta_y) + 1

# Initialize image
output_image_array = np.zeros((tile_size * num_tiles_y, tile_size * num_tiles_x), dtype=np.float32)

# Download and paste tiles
total_tiles = num_tiles_x * num_tiles_y

with tqdm(total=total_tiles) as pbar:
    for i in range(num_tiles_x):
        for j in range(num_tiles_y):
            tile_bbox = (bbox_utm[0] + i * delta_x, bbox_utm[1] + (num_tiles_y - j - 1) * delta_y, bbox_utm[0] + (i + 1) * delta_x, bbox_utm[1] + (num_tiles_y - j) * delta_y)
            tile = download_tile(tile_bbox, tile_size, tile_size)
            tile_array = np.array(tile)
            output_image_array[j * tile_size:(j + 1) * tile_size, i * tile_size:(i + 1) * tile_size] = tile_array
            pbar.update(1)

# Define geospatial properties
transform = from_origin(bbox_utm[0], bbox_utm[3], resolution, resolution)

# Save as a GeoTIFF file
with rasterio.open(output_filename, 'w', driver='GTiff',
                    height=output_image_array.shape[0], width=output_image_array.shape[1], count=1,
                    dtype=str(output_image_array.dtype),
                    crs='+proj=utm +zone=33 +ellps=WGS84 +datum=WGS84 +units=m +no_defs',
                    transform=transform) as dst:
    dst.write(output_image_array, 1)

print(f"Image saved as GeoTIFF at {output_filename}.")

# Directory where the .tif files are stored
output_dir = "../Output"

# Find the most recently created .tif file
latest_file = max(
    (os.path.join(output_dir, filename) for filename in os.listdir(output_dir) if filename.endswith('.tif')),
    key=os.path.getctime
)

# Open the GeoTIFF
with rasterio.open(latest_file) as src:
    # Read the data
    data = src.read()
    print("Data shape:", data.shape)

# Calculate and print statistics
print("Min:", np.min(data))
print("Max:", np.max(data))
print("Mean:", np.mean(data))
print("Standard deviation:", np.std(data))

# Normalize the data to 0-255
data_normalized = ((data - data.min()) / (data.max() - data.min()) * 255).astype(np.uint8)

# Save the normalized data as a new GeoTIFF file
output_normalized_filename = os.path.join(output_dir, "height_normalized_{:04d}.tif".format(next_file_number))
print(f"Saving the normalized data as a new GeoTIFF file at {output_normalized_filename}...")
with rasterio.open(output_normalized_filename, 'w', driver='GTiff',
                    height=data_normalized.shape[1], width=data_normalized.shape[2], count=1,
                    dtype=str(data_normalized.dtype),
                    crs='+proj=utm +zone=33 +ellps=WGS84 +datum=WGS84 +units=m +no_defs',
                    transform=transform) as dst:
    dst.write(data_normalized, 1)
print(f"Normalized data saved as GeoTIFF at {output_normalized_filename}.")
