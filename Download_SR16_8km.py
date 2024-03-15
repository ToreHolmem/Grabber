import requests
from owslib.wms import WebMapService
from PIL import Image
from io import BytesIO
import rasterio
from rasterio.transform import from_origin
import argparse
import math

# Parse command line arguments
parser = argparse.ArgumentParser()
parser.add_argument("center_lat", type=float, help="Center latitude")
parser.add_argument("center_lon", type=float, help="Center longitude")
parser.add_argument("output_location", type=str, help="Output location")
args = parser.parse_args()

def download_SR16_4km(center_lat, center_lon, output_location):
    try:
        print("Connecting to WMS service...")
        wms = WebMapService('https://wms.nibio.no/cgi-bin/sr16?VERSION=1.3.0&SERVICE=WMS&REQUEST=GetCapabilities')

        print("Calculating bounding box...")
        half_size_meters = 2050  # half size in meters

        # Convert meters to degrees
        km_per_degree = 111.32  # average km per degree latitude in Norway
        half_size_lat = half_size_meters / (km_per_degree * 1000)
        half_size_lon = half_size_meters / (km_per_degree * 1000 * math.cos(math.radians(center_lat)))

        min_x = center_lon - half_size_lon
        max_x = center_lon + half_size_lon
        min_y = center_lat - half_size_lat
        max_y = center_lat + half_size_lat

        # New print statements
        print(f"Bounding box: ({min_x}, {min_y}, {max_x}, {max_y})")
        print("Spatial reference system: EPSG:25833")


        print("Requesting image from WMS...")
        img = wms.getmap(layers=['SRRTRESLAG'],
                         srs='EPSG:25833',
                         bbox=(min_x, min_y, max_x, max_y),
                         size=(256, 256),
                         format='image/tiff')

        print("Saving image...")
        output_file = f"{output_location}/sr16_15_SRRTRESLAG_4km_download.tiff"
        with open(output_file, 'wb') as out:
            out.write(img.read())

        print("Image saved successfully.")

    except Exception as e:
        print(f"An error occurred: {e}")

# Use command line arguments instead of hard-coded values
download_SR16_4km(args.center_lat, args.center_lon, args.output_location)
