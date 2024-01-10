from owslib.wcs import WebCoverageService
import rasterio
import numpy as np
import os
from rasterio.io import MemoryFile
from pyproj import CRS, Transformer
import argparse
from rasterio.merge import merge
import imageio
from concurrent.futures import ThreadPoolExecutor

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

# The total width and height of the area
total_width = 60000
total_height = 60000

# The width and height of each quadrant
quadrant_width = total_width / 4
quadrant_height = total_height / 4

# The list of quadrants (files)
quadrant_files = []

# The list of quadrants (files)
quadrant_files = []

# Function to handle download and processing of a quadrant
def process_quadrant(i, j):
    # Calculate the bounding box (minx, miny, maxx, maxy) for the quadrant
    bbox = (
        center_x - total_width / 2 + i * quadrant_width,  # minx
        center_y - total_height / 2 + j * quadrant_height,  # miny
        center_x - total_width / 2 + (i + 1) * quadrant_width,  # maxx
        center_y - total_height / 2 + (j + 1) * quadrant_height,  # maxy
    )

    # Request the coverage for the quadrant
    response = wcs.getCoverage(
        identifier=coverage_id,
        bbox=bbox,
        crs='EPSG:25833',
        format='GeoTIFF',
        resx=10,  # Adjust resolution to maintain an output of about 1500px per quadrant
        resy=10
    )

    # Save the response to a GeoTIFF file
    with MemoryFile(response.read()) as memfile:
        with memfile.open() as dataset:
            # Save the quadrant GeoTIFF
            quadrant_geotiff_path = os.path.join(args.output_location, f'quadrant_{i}_{j}_32b.tif')
            quadrant_files.append(quadrant_geotiff_path)
            with rasterio.open(quadrant_geotiff_path, 'w', **dataset.profile) as dst:
                dst.write(dataset.read())

# Create a ThreadPoolExecutor
with ThreadPoolExecutor(max_workers=8) as executor:
    # For each quadrant
    for i in range(4):
        for j in range(4):
            executor.submit(process_quadrant, i, j)

# List to store each raster data array and its associated transform
src_files_to_mosaic = []

# Open each quadrant file, and store the raster data array and its associated transform
for fp in quadrant_files:
    src = rasterio.open(fp)
    src_files_to_mosaic.append(src)

# Merge function returns a single mosaic array and the transformation info
mosaic, out_trans = merge(src_files_to_mosaic)

# Copy the metadata
out_meta = src.meta.copy()

# Update the metadata
out_meta.update({"driver": "GTiff",
                 "height": mosaic.shape[1],
                 "width": mosaic.shape[2],
                 "transform": out_trans,
                 "crs": epsg25833})

# Write the mosaic raster to disk
with rasterio.open(os.path.join(args.output_location, 'height_60km.tif'), "w", **out_meta) as dest:
    dest.write(mosaic)

# Close the datasets
for src in src_files_to_mosaic:
    src.close()

# Delete the quadrant files
for quadrant_file in quadrant_files:
    os.remove(quadrant_file)

# Unused functionality of saving the geotif file to a more legible 16-bit png

## Open the merged GeoTIFF file
#with rasterio.open(os.path.join(args.output_location, 'heightmap_32b_60km.tiff'), 'r') as src:
#    # Read the pixel values
#    pixel_array = src.read(1)

#    # Define the known range of the dataset
#    min_height = -4
#    max_height = 2500

#    # Normalize the pixel values to the range 0 - 65535
#    normalized_array = ((pixel_array - min_height) / (max_height - min_height)) * 65535

#    # Handle NaN values
#    normalized_array = np.nan_to_num(normalized_array, nan=0)

#    # Convert the normalized array to 16-bit unsigned integer
#    uint16_array = normalized_array.astype(np.uint16)

## Write the data to a 16-bit PNG file
#imageio.imwrite(os.path.join(args.output_location, 'heightmap_16b_60km.png'), uint16_array)