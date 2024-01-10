import os
import sys
from math import cos, pi
import requests
from PIL import Image
from io import BytesIO

center_lat = 62.46759643205735
center_lon = 6.248639450722139
half_size = 4 * 1000 / 2  # 4 km across, in meters

min_x = center_lon - half_size / (111.32 * 1000 * cos(center_lat * pi / 180))
max_x = center_lon + half_size / (111.32 * 1000 * cos(center_lat * pi / 180))
min_y = center_lat - half_size / (111.32 * 1000)
max_y = center_lat + half_size / (111.32 * 1000)

resolution = 1.75  # meters per pixel at zoom level 13
width = int((max_x - min_x) * 111.32 * 1000 * cos(center_lat * pi / 180) / resolution)
height = int((max_y - min_y) * 111.32 * 1000 / resolution)

image_url = 'https://services.geodataonline.no/arcgis/rest/services/Geocache_UTM33_EUREF89/GeocacheBilder/MapServer/export?bbox={},{},{},{}&bboxSR=4326&imageSR=32633&size={},{}&format=png&transparent=true&f=image'.format(min_x, min_y, max_x, max_y, width, height)

output_file = "output_image.tif"

os.system(f"gdal_translate -of GTiff '{image_url}' {output_file}")

print("Image saved as", output_file)
