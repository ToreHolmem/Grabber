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
from tqdm import tqdm

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
    image_url = 'https://services.geodataonline.no/arcgis/rest/services/Geocache_UTM33_EUREF89/GeocacheBilder/MapServer/export?bbox={},{},{},{}&bboxSR=25833&imageSR=25833&size={},{}&format=png&transparent=false&f=image'.format(*bbox, width, height)
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
        pbar.update(1)
        q.task_done()

# part 2: set up input parameters
center_lat = args.center_lat
center_lon = args.center_lon
half_size = (0.5 + 0.2) * 1024


min_x = center_lon - half_size / (111.32 * 1000 * cos(center_lat * pi / 180))
max_x = center_lon + half_size / (111.32 * 1000 * cos(center_lat * pi / 180))
min_y = center_lat - half_size / (111.32 * 1000)
max_y = center_lat + half_size / (111.32 * 1000)

bbox = (min_x, min_y, max_x, max_y)
bbox_utm = transform_bbox(bbox, "epsg:4326", "epsg:25833")

# Define the list of resolutions
resolutions = [
    21674.7100160867, 10837.35500804335, 5418.677504021675, 2709.3387520108377,
    1354.6693760054188, 677.3346880027094, 338.6673440013547, 169.33367200067735,
    84.66683600033868, 42.33341800016934, 21.16670900008467, 10.583354500042335,
    5.291677250021167, 2.6458386250105836, 1.3229193125052918, 0.6614596562526459,
    0.33072982812632296, 0.16536491406316148
]

# Define the zoom level
zoom_level = 17  # Set your desired zoom level

# Get the resolution for the chosen zoom level
resolution = resolutions[zoom_level]

print(f"Resolution for Zoom Level {zoom_level}: {resolution}")

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

pbar = tqdm(total=total_tiles, desc="Merging tiles", ncols=100)
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
    pbar.close()


# Define the CRS
crs = rasterio.crs.CRS.from_string("EPSG:25833")

# Define the geotransformation (assuming north-up) -- NEW METHOD
pixel_resolution = resolution  # which is meters per pixel at the desired zoom level
transform = from_origin(bbox_utm[0], bbox_utm[1] + (tile_size * num_tiles_y * pixel_resolution), pixel_resolution, pixel_resolution)


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


