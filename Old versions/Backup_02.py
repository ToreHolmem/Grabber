import os
import sys
from math import cos, pi
import requests
from PIL import Image
from io import BytesIO
import pyproj

def download_tile(bbox, width, height):
    image_url = 'https://services.geodataonline.no/arcgis/rest/services/Geocache_UTM33_EUREF89/GeocacheBilder/MapServer/export?bbox={},{},{},{}&bboxSR=32633&imageSR=32633&size={},{}&format=png&transparent=false&f=image'.format(*bbox, width, height)
    response = requests.get(image_url)
    return Image.open(BytesIO(response.content))

def transform_bbox(bbox, src_crs, dst_crs):
    transformer = pyproj.Transformer.from_crs(src_crs, dst_crs, always_xy=True)
    min_x, min_y = transformer.transform(bbox[0], bbox[1])
    max_x, max_y = transformer.transform(bbox[2], bbox[3])
    return (min_x, min_y, max_x, max_y)

center_lat = 62.47481623447284
center_lon = 6.245537627390876
half_size = 4 * 1000 / 2  # 2.5 km across, in meters

min_x = center_lon - half_size / (111.32 * 1000 * cos(center_lat * pi / 180))
max_x = center_lon + half_size / (111.32 * 1000 * cos(center_lat * pi / 180))
min_y = center_lat - half_size / (111.32 * 1000)
max_y = center_lat + half_size / (111.32 * 1000)

bbox = (min_x, min_y, max_x, max_y)
bbox_utm = transform_bbox(bbox, "epsg:4326", "epsg:32633")

resolution = 1.75  # meters per pixel at zoom level 13
tile_size = 256  # number of pixels per tile

delta_x = resolution * tile_size
delta_y = resolution * tile_size

num_tiles_x = int((bbox_utm[2] - bbox_utm[0]) / delta_x) + 1
num_tiles_y = int((bbox_utm[3] - bbox_utm[1]) / delta_y) + 1

output_image = Image.new('RGB', (tile_size * num_tiles_x, tile_size * num_tiles_y))

total_tiles = num_tiles_x * num_tiles_y
tile_counter = 1

for i in range(num_tiles_x):
    for j in range(num_tiles_y):
        print(f"Processing tile {tile_counter}/{total_tiles}...")
        tile_bbox = (bbox_utm[0] + i * delta_x, bbox_utm[1] + (num_tiles_y - j - 1) * delta_y, bbox_utm[0] + (i + 1) * delta_x, bbox_utm[1] + (num_tiles_y - j) * delta_y)
        tile = download_tile(tile_bbox, tile_size, tile_size)
        output_image.paste(tile, (i * tile_size, j * tile_size))
        print(f"Tile {tile_counter}/{total_tiles} processed.")
        tile_counter += 1

# Save the stitched image
output_image.save('stitched_image.png')

print("Stitched operation done")
