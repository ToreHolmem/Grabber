import os
import sys
from math import ceil, cos, pi
import requests
import argparse
from PIL import Image
from io import BytesIO
import pyproj
import threading
from queue import Queue
import time

# part 0: parse arguments

parser = argparse.ArgumentParser()
parser.add_argument("center_lat", type=float)
parser.add_argument("center_lon", type=float)
parser.add_argument("output_location", type=str)
args = parser.parse_args()

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
half_size = 0.5 * 60000  # Set size to 60 km

min_x = center_lon - half_size / (111.32 * 1000 * cos(center_lat * pi / 180))
max_x = center_lon + half_size / (111.32 * 1000 * cos(center_lat * pi / 180))
min_y = center_lat - half_size / (111.32 * 1000)
max_y = center_lat + half_size / (111.32 * 1000)

bbox = (min_x, min_y, max_x, max_y)
bbox_utm = transform_bbox(bbox, "epsg:4326", "epsg:32633")

zoom_level = 11  # Set your desired zoom level to Level ID 11
resolution_base = 10.583354500042335  # meters per pixel at zoom level 11

# We don't need to recalculate the resolution, as we want to use the one provided by the service
resolution = resolution_base

tile_size = 256  # number of pixels per tile

# Calculate the number of tiles to cover the whole area
num_tiles_x = int(ceil((bbox_utm[2] - bbox_utm[0]) / (resolution * tile_size)))
num_tiles_y = int(ceil((bbox_utm[3] - bbox_utm[1]) / (resolution * tile_size)))

output_image = Image.new('RGB', (tile_size * num_tiles_x, tile_size * num_tiles_y))

total_tiles = num_tiles_x * num_tiles_y
tile_counter = 0

# part 3: download and merge tiles

print("Merging tiles into final image...")
start_time = time.time() # start timing

# part 4: Create a queue of tiles to be processed
tile_queue = Queue()
for i in range(num_tiles_x):
    for j in range(num_tiles_y):
        tile_bbox = (bbox_utm[0] + i * resolution * tile_size, bbox_utm[1] + (num_tiles_y - j - 1) * resolution * tile_size, bbox_utm[0] + (i + 1) * resolution * tile_size, bbox_utm[1] + (num_tiles_y - j) * resolution * tile_size)
        tile_queue.put((i, j, tile_bbox))

# part 5: Create and start worker threads to download and process tiles
num_workers = 6 # Set the number of worker threads
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

# part 8: Save the stitched image
output_image_path = os.path.join(args.output_location, 'stitched_image_aerial.png')

output_image.save(output_image_path)

end_time = time.time() # stop timing
print(f"Image merging took {1000 * (end_time - start_time):.2f} milliseconds.")

# part 9: Crop the image to a square of size 6000x6000 with the original center
print("Cropping image...")
start_time = time.time() # start timing

# Calculate the total width and height of the image
total_width = tile_size * num_tiles_x
total_height = tile_size * num_tiles_y

# Calculate the center of the image
center_x = total_width // 2
center_y = total_height // 2

# Set the desired half size
desired_half_size = 3000

# If the total width or height of the image is less than the desired size,
# adjust the half size to half the total width or height, whichever is smaller.
if total_width < desired_half_size * 2 or total_height < desired_half_size * 2:
    half_size = min(total_width, total_height) // 2
else:
    half_size = desired_half_size

# Calculate the crop box
crop_bbox = (center_x - half_size, center_y - half_size, center_x + half_size, center_y + half_size)

output_image = output_image.crop(crop_bbox)
output_image_path = os.path.join(args.output_location, 'Final_Aerial_6000px.png')
output_image.save(output_image_path)

# part 10: print time
end_time = time.time() # stop timing
print(f"Image cropping took {1000 * (end_time - start_time):.2f} milliseconds.")

print("All done!")

# part 11: Open the final image in viewer
#output_image.show()
