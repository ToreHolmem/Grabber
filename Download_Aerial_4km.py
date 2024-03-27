import os
import requests
import argparse
from PIL import Image
from io import BytesIO
import threading
from queue import Queue
from tqdm import tqdm
import rasterio
from rasterio.transform import from_origin
import numpy as np

# print this script is called "Download_Aerial_4km.py" and is used to download aerial imagery data for a 4 km x 4 km bounding box.

# Updated argparse to include temp_dir and final_output_path
parser = argparse.ArgumentParser(description="Download aerial imagery data for a specific bounding box.")
parser.add_argument("min_x", type=float, help="Minimum X coordinate of the bounding box.")
parser.add_argument("min_y", type=float, help="Minimum Y coordinate of the bounding box.")
parser.add_argument("max_x", type=float, help="Maximum X coordinate of the bounding box.")
parser.add_argument("max_y", type=float, help="Maximum Y coordinate of the bounding box.")
parser.add_argument("temp_dir", type=str, help="Temporary directory path for storing intermediate files.")
parser.add_argument("final_output_path", type=str, help="Path to save the final stitched image.")
args = parser.parse_args()

print("Arguments parsed")



# Define helper functions
def download_tile(bbox, width, height):
    image_url = 'https://services.geodataonline.no/arcgis/rest/services/Geocache_UTM33_EUREF89/GeocacheBilder/MapServer/export?bbox={},{},{},{}&bboxSR=25833&imageSR=25833&size={},{}&format=png&transparent=false&f=image'.format(*bbox, width, height)
    response = requests.get(image_url)
    return Image.open(BytesIO(response.content))

print("Helper functions defined")

def tile_worker(q, output_image, tile_size):
    while True:
        tile_info = q.get()
        if tile_info is None:
            q.task_done()
            break
        i, j, tile_bbox = tile_info
        tile = download_tile(tile_bbox, tile_size, tile_size)
        output_image.paste(tile, (i * tile_size, j * tile_size))
        pbar.update(1)  # Update the progress bar here
        q.task_done()

print("Tile worker defined")

# Use the passed bounding box directly
bbox = (args.min_x, args.min_y, args.max_x, args.max_y)

print("Bounding box defined")

# Define the list of resolutions
resolutions = [
    21674.7100160867, 10837.35500804335, 5418.677504021675, 2709.3387520108377,
    1354.6693760054188, 677.3346880027094, 338.6673440013547, 169.33367200067735,
    84.66683600033868, 42.33341800016934, 21.16670900008467, 10.583354500042335,
    5.291677250021167, 2.6458386250105836, 1.3229193125052918, 0.6614596562526459,
    0.33072982812632296, 0.16536491406316148
]

print ("Resolutions defined")

zoom_level = 15  # or another value as required
resolution = resolutions[zoom_level]
tile_size = 256
delta_x = resolution * tile_size
delta_y = resolution * tile_size
num_tiles_x = int((bbox[2] - bbox[0]) / delta_x) + 1
num_tiles_y = int((bbox[3] - bbox[1]) / delta_y) + 1

print("Zoom level, resolution, tile size, delta x, delta y, num tiles x, num tiles y defined")

# Initialize the progress bar
total_tiles = num_tiles_x * num_tiles_y
pbar = tqdm(total=total_tiles, desc="Downloading and processing tiles")

print("Progress bar initialized")

# Prepare for tile download and stitching
output_image = Image.new('RGB', (tile_size * num_tiles_x, tile_size * num_tiles_y))
tile_queue = Queue()
for i in range(num_tiles_x):
    for j in range(num_tiles_y):
        tile_bbox = (bbox[0] + i * delta_x, bbox[1] + (num_tiles_y - j - 1) * delta_y, bbox[0] + (i + 1) * delta_x, bbox[1] + (num_tiles_y - j) * delta_y)
        tile_queue.put((i, j, tile_bbox))

print("Tile download and stitching prepared")

# Start worker threads for tile downloading and processing
num_workers = 64
workers = [threading.Thread(target=tile_worker, args=(tile_queue, output_image, tile_size)) for _ in range(num_workers)]
for worker in workers:
    worker.start()

print("Worker threads started")

# Add this block to put a termination signal (None) for each worker
for _ in range(num_workers):
    tile_queue.put(None)  # Signal for each worker thread to terminate

# Wait for all tiles to be processed and workers to finish
tile_queue.join()

# Join all worker threads to ensure they have finished
for worker in workers:
    worker.join()

print("All tiles processed and workers finished")

# Saving the stitched image
crs = rasterio.crs.CRS.from_string("EPSG:25833")
transform = from_origin(bbox[0], bbox[1] + (tile_size * num_tiles_y * resolution), resolution, resolution)
profile = {
    'driver': 'GTiff',
    'height': output_image.height,
    'width': output_image.width,
    'count': 3,
    'dtype': rasterio.uint8,
    'crs': crs,
    'transform': transform,
}

print("GeoTIFF profile defined")

output_image_path = args.final_output_path
with rasterio.open(output_image_path, 'w', **profile) as dst:
    output_array = np.array(output_image)
    for band in range(output_array.shape[2]):
        dst.write(output_array[:, :, band], band + 1)