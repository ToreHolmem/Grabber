import os
import sys
from math import cos, pi
import requests
import argparse
from PIL import Image
from io import BytesIO
import pyproj
import threading
from queue import Queue
import time
import rasterio
from rasterio.transform import from_origin
import numpy as np

# part 0: parse arguments
parser = argparse.ArgumentParser()
parser.add_argument("center_lat", type=float)
parser.add_argument("center_lon", type=float)
parser.add_argument("output_location", type=str)
args = parser.parse_args()

print(f"Center Latitude: {args.center_lat}")
print(f"Center Longitude: {args.center_lon}")

# part 1: define helper functions

def download_tile(bbox, width, height):
    image_url = 'https://services.geodataonline.no/arcgis/rest/services/Geocache_UTM33_EUREF89/GeocacheBilder/MapServer/export?bbox={},{},{},{}&bboxSR=32633&imageSR=32633&size={},{}&format=png&transparent=false&f=image'.format(*bbox, width, height)
    response = requests.get(image_url)
    return Image.open(BytesIO(response.content))

def transform_bbox(bbox, src_crs, dst_crs):
    transformer = pyproj.Transformer.from_crs(src_crs, dst_crs, always_xy=True)
    min_x, min_y = transformer.transform(bbox[0], bbox[1])
    max_x, max_y = transformer.transform(bbox[2], bbox[3])
    return (min_x, min_y, max_x, max_y)

def tile_worker(q, output_image, tile_size):
    while True:
        tile_info = q.get()
        if tile_info is None:
            q.task_done()
            break
        i, j, tile_bbox = tile_info
        tile = download_tile(tile_bbox, tile_size, tile_size)
        output_image.paste(tile, (i * tile_size, j * tile_size))
        print(f"Tile ({i}, {j}) processed.")
        q.task_done()

# part 2: set up input parameters

center_lat = args.center_lat
center_lon = args.center_lon
half_size = 0.5 * 1024  # Set size

min_x = center_lon - half_size / (111.32 * 1000 * cos(center_lat * pi / 180))
max_x = center_lon + half_size / (111.32 * 1000 * cos(center_lat * pi / 180))
min_y = center_lat - half_size / (111.32 * 1000)
max_y = center_lat + half_size / (111.32 * 1000)

bbox = (min_x, min_y, max_x, max_y)
bbox_utm = transform_bbox(bbox, "epsg:4326", "epsg:32633")

zoom_level = 18  # Set your desired zoom level (e.g., 18 for max resolution)
resolution_base = 0.16536491406316148  # meters per pixel at zoom level 18
resolution = resolution_base * (2**(18 - zoom_level))  # Calculate resolution for the desired zoom level

tile_size = 256  # number of pixels per tile

delta_x = resolution * tile_size
delta_y = resolution * tile_size

num_tiles_x = int((bbox_utm[2] - bbox_utm[0]) / delta_x) + 1
num_tiles_y = int((bbox_utm[3] - bbox_utm[1]) / delta_y) + 1

output_image = Image.new('RGB', (tile_size * num_tiles_x, tile_size * num_tiles_y))

total_tiles = num_tiles_x * num_tiles_y
tile_counter = 0

print(f"BBox (WGS84): {bbox}")
print(f"BBox (UTM33): {bbox_utm}")
print(f"Resolution: {resolution} meters per pixel")
print(f"Delta X: {delta_x}, Delta Y: {delta_y}")
print(f"Number of Tiles (X): {num_tiles_x}, Number of Tiles (Y): {num_tiles_y}")

# part 3: download and merge tiles

print("Merging tiles into final image...")
start_time = time.time() # start timing
output_image = Image.new('RGB', (tile_size * num_tiles_x, tile_size * num_tiles_y))
total_tiles = num_tiles_x * num_tiles_y
tile_counter = 0

# part 4: Create a queue of tiles to be processed
tile_queue = Queue()
for i in range(num_tiles_x):
    for j in range(num_tiles_y):
        tile_bbox = (bbox_utm[0] + i * delta_x, bbox_utm[1] + (num_tiles_y - j - 1) * delta_y, bbox_utm[0] + (i + 1) * delta_x, bbox_utm[1] + (num_tiles_y - j) * delta_y)
        tile_queue.put((i, j, tile_bbox))
        tile_counter += 1

# part 5: Create and start worker threads to download and process tiles
num_workers = 64 # Set the number of worker threads
workers = []
for _ in range(num_workers):
    worker = threading.Thread(target=tile_worker, args=(tile_queue, output_image, tile_size))
    worker.start()
    workers.append(worker)

# part 6: Wait for all tiles to be processed
tile_queue.join()

# part 7: Stop the worker threads
for _ in range(num_workers):
    tile_queue.put(None)
for worker in workers:
    worker.join()

# Define the CRS
crs = rasterio.crs.CRS.from_string("EPSG:32633")

# Define the geotransformation (assuming north-up)
transform = from_origin(bbox_utm[0], bbox_utm[3], delta_x, delta_y)
print("Transform:", transform) # Print the transform

# Define the profile (metadata)
profile = {
    'driver': 'GTiff',
    'height': output_image.height,
    'width': output_image.width,
    'count': 3, # Assuming an RGB image
    'dtype': rasterio.uint8,
    'crs': crs,
    'transform': transform,
}

print("Profile:", profile) # Print the profile

# Convert the PIL image to a NumPy array
output_array = np.array(output_image)

# Save as a PNG file
output_image_path = os.path.join(args.output_location, 'aerial_image.png')
output_image.save(output_image_path)
print(f"PNG saved to {output_image_path}")

# Reorder the bands so that they are in the order expected by rasterio
#output_array = output_array[:, :, [2, 1, 0]]

# Write the GeoTIFF file
output_image_path = os.path.join(args.output_location, 'aerial_1km_download.tif')
with rasterio.open(output_image_path, 'w', **profile) as dst:
    for band in range(output_array.shape[2]):
        dst.write(output_array[:, :, band], band + 1)

print(f"GeoTIFF saved to {output_image_path}")

# part 10: print time
end_time = time.time() # stop timing
print(f"Image cropping took {1000 * (end_time - start_time):.2f} milliseconds.")

print("All done!")

print("Aerial GeoTIFF Information:")
print(f"  CRS: {crs}")
print(f"  Transform: {transform}")
print(f"  Width: {output_image.width}, Height: {output_image.height}")
print(f"  Pixel Size: {delta_x} meters, {delta_y} meters")


