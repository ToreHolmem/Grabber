from owslib.wcs import WebCoverageService
import rasterio
import numpy as np
import os
from rasterio.io import MemoryFile
from pyproj import CRS, Transformer
import argparse

# Parse arguments

parser = argparse.ArgumentParser()
parser.add_argument("center_lat", type=float)
parser.add_argument("center_lon", type=float)
parser.add_argument("output_location", type=str)
args = parser.parse_args()

# Specify the WCS endpoint url
url = 'https://wcs.geonorge.no/skwms1/wcs.hoyde-dtm-nhm-25833?service=wcs&request=getcapabilities'

# Connect to the WCS service
wcs = WebCoverageService(url, version='1.0.0')

# Specify the coverage id
coverage_id = 'nhm_dtm_topo_25833'

# Center point (latitude, longitude)
center_lat, center_lon = args.center_lat, args.center_lon

# Define the coordinate systems
wgs84 = CRS('EPSG:4326')  # WGS84
epsg25833 = CRS('EPSG:25833')  # UTM zone 33N

# Define the transformer
transformer = Transformer.from_crs(wgs84, epsg25833)

# Convert center point to EPSG:25833
center_x, center_y = transformer.transform(center_lat, center_lon)

# Calculate the bounding box (minx, miny, maxx, maxy)
bbox = (
    center_x - 512,  # minx
    center_y - 512,  # miny
    center_x + 512,  # maxx
    center_y + 512,  # maxy
)

# Specify the output CRS (coordinate reference system) and format
# Note: The output CRS should match the CRS of the coverage
output_crs = 'EPSG:25833'
format = 'GeoTIFF'

# Request the coverage
response = wcs.getCoverage(
    identifier='nhm_dtm_topo_25833',
    bbox=bbox,
    crs='EPSG:25833',
    format='GeoTIFF',
    resx=1,
    resy=1
)

# Save the response to a GeoTIFF file
with MemoryFile(response.read()) as memfile:
    with memfile.open() as dataset:
        # Save the original GeoTIFF
        original_geotiff_path = os.path.join(args.output_location, 'heightmap_32b_1024_Meters.tif')
        with rasterio.open(original_geotiff_path, 'w', **dataset.profile) as original_dst:
            original_dst.write(dataset.read())

        # Save the processed GeoTIFF
        processed_geotiff_path = os.path.join(args.output_location, 'temp_heightmap_1km_geoTIFF.tif')
        with rasterio.open(processed_geotiff_path, 'w', **dataset.profile) as processed_dst:
            processed_dst.write(dataset.read())

# Open the input GeoTIFF file that needs conversion
input_file = os.path.join(args.output_location, 'temp_heightmap_1km_geoTIFF.tif')
output_file = os.path.join(args.output_location, 'heightmap_16b_1024_Meters.png')

with rasterio.open(input_file, 'r') as src:
    # Read the pixel values
    pixel_array = src.read(1)

    # Define the known range of the dataset
    min_height = -4
    max_height = 2500

    # Normalize the pixel values to the range 0 - 65535
    normalized_array = ((pixel_array - min_height) / (max_height - min_height)) * 65535

    # Handle NaN values
    normalized_array = np.nan_to_num(normalized_array, nan=0)

    # Convert the normalized array to 16-bit unsigned integer
    uint16_array = normalized_array.astype(np.uint16)

    # Create the output TIFF file
    profile = src.profile
    profile.update(dtype=rasterio.uint16)

    with rasterio.open(output_file, 'w', **profile) as dst:
        dst.write(uint16_array, 1)

# Delete the input GeoTIFF file
if os.path.exists(input_file):
    os.remove(input_file)
