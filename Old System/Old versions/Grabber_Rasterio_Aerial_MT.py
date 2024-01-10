# This code doesn´t work, there is something wrong in the multi-process stuff..

import concurrent.futures
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


# Create the output directory if it doesn't exist
output_dir = "../Output"
print(f"Creating output directory {output_dir} if it doesn't exist...")
os.makedirs(output_dir, exist_ok=True)
print(f"Output directory {output_dir} created or already exists.")

# Find the highest existing filename
print("Finding the highest existing filename...")
files = glob.glob(os.path.join(output_dir, "Aerial_*.tif"))
if not files:
    # No files, start from 0001
    print("No previous files found. Starting from 0001.")
    next_file_number = 1
else:
    # Get the file number part of the filename, convert to int and get the max
    max_file_number = max(int(os.path.splitext(os.path.basename(file))[0].split('_')[1]) for file in files)
    next_file_number = max_file_number + 1
    print(f"Previous files found. Continuing from {next_file_number:04d}.")

# Create the output filename with the next file number
output_filename = os.path.join(output_dir, "Aerial_{:04d}.tif".format(next_file_number))
print(f"Output filename set as {output_filename}")

# Helper functions
def download_tile(bbox, width, height):
    print(f"Downloading tile for bounding box {bbox}...")
    image_url = 'https://services.geodataonline.no/arcgis/rest/services/Geocache_UTM33_EUREF89/GeocacheBilder/MapServer/export?bbox={},{},{},{}&bboxSR=32633&imageSR=32633&size={},{}&format=png&transparent=false&f=image'.format(*bbox, width, height)
    response = requests.get(image_url)
    print(f"Downloaded tile for bounding box {bbox}")
    return Image.open(BytesIO(response.content))

def transform_bbox(bbox, src_crs, dst_crs):
    print(f"Transforming bounding box {bbox} from {src_crs} to {dst_crs}...")
    transformer = pyproj.Transformer.from_crs(src_crs, dst_crs, always_xy=True)
    min_x, min_y = transformer.transform(bbox[0], bbox[1])
    max_x, max_y = transformer.transform(bbox[2], bbox[3])
    print(f"Transformed bounding box to {min_x, min_y, max_x, max_y} in {dst_crs}")
    return (min_x, min_y, max_x, max_y)

# Parameters
center_lat = 62.45420359364632
center_lon = 7.668951948534192
half_size = 0.5 * 1000 / 2  # Set size

# Calculate bounding box
print("Calculating bounding box...")
min_x = center_lon - half_size / (111.32 * 1000 * cos(center_lat * pi / 180))
max_x = center_lon + half_size / (111.32 * 1000 * cos(center_lat * pi / 180))
min_y = center_lat - half_size / (111.32 * 1000)
max_y = center_lat + half_size / (111.32 * 1000)

bbox = (min_x, min_y, max_x, max_y)
print(f"Bounding box calculated: {bbox}")
bbox_utm = transform_bbox(bbox, "epsg:4326", "epsg:32633")
print(f"Bounding box transformed to UTM: {bbox_utm}")

zoom_level = 18  # Set your desired zoom level (e.g., 18 for max resolution)
resolution_base = 0.1  # meters per pixel at zoom level 18
resolution = resolution_base * (2**(18 - zoom_level))  # Calculate resolution for the desired zoom level

tile_size = 256  # number of pixels per tile

delta_x = resolution * tile_size
delta_y = resolution * tile_size

num_tiles_x = int((bbox_utm[2] - bbox_utm[0]) / delta_x) + 1
num_tiles_y = int((bbox_utm[3] - bbox_utm[1]) / delta_y) + 1

print(f"Number of tiles to download: {num_tiles_x} in x direction, {num_tiles_y} in y direction")

# Initialize image
print("Initializing the output image...")
output_image = Image.new('RGB', (tile_size * num_tiles_x, tile_size * num_tiles_y))
print(f"Output image initialized with size {(tile_size * num_tiles_x, tile_size * num_tiles_y)}")

# Download and paste tiles
def download_and_paste_tile(i, j):
    tile_bbox = (bbox_utm[0] + i * delta_x, bbox_utm[1] + (num_tiles_y - j - 1) * delta_y, bbox_utm[0] + (i + 1) * delta_x, bbox_utm[1] + (num_tiles_y - j) * delta_y)
    print(f"Downloading tile {i+1} of {num_tiles_x} in x direction, {j+1} of {num_tiles_y} in y direction")
    tile = download_tile(tile_bbox, tile_size, tile_size)
    print(f"Pasting tile {i+1} of {num_tiles_x} in x direction, {j+1} of {num_tiles_y} in y direction")
    output_image.paste(tile, (i * tile_size, j * tile_size))

with concurrent.futures.ProcessPoolExecutor() as executor:
    futures = [executor.submit(download_and_paste_tile, i, j) for i in range(num_tiles_x) for j in range(num_tiles_y)]
    concurrent.futures.wait(futures)

# Convert PIL Image to Numpy array and close PIL Image
print("Converting the output image to a Numpy array...")
output_image_array = np.array(output_image)
print("Closing the PIL Image...")
output_image.close()

# Define geospatial properties
print("Defining geospatial properties...")
transform = from_origin(bbox_utm[0], bbox_utm[3], resolution, resolution)

# Save as a GeoTIFF file
print("Saving the image as a GeoTIFF file...")
with rasterio.open(output_filename, 'w', driver='GTiff',
                    height=output_image_array.shape[0], width=output_image_array.shape[1], count=3,
                    dtype=str(output_image_array.dtype),
                    crs='+proj=utm +zone=33 +ellps=WGS84 +datum=WGS84 +units=m +no_defs',
                    transform=transform) as dst:
    dst.write(output_image_array.transpose((2, 0, 1)))

print(f"Image saved as GeoTIFF at {output_filename}.")
