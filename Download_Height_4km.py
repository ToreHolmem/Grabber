from owslib.wcs import WebCoverageService
import rasterio
import numpy as np
import os
from rasterio.io import MemoryFile
import argparse
from rasterio.merge import merge
from concurrent.futures import ThreadPoolExecutor
import shutil

# Parse arguments
parser = argparse.ArgumentParser(description='Download height data and process it into a single GeoTIFF.')
parser.add_argument("min_x", type=float, help="Minimum X coordinate of the bounding box.")
parser.add_argument("min_y", type=float, help="Minimum Y coordinate of the bounding box.")
parser.add_argument("max_x", type=float, help="Maximum X coordinate of the bounding box.")
parser.add_argument("max_y", type=float, help="Maximum Y coordinate of the bounding box.")
parser.add_argument("temp_dir", type=str, help="Temporary directory path for storing intermediate files.")
parser.add_argument("final_output_path", type=str, help="Path to save the final merged GeoTIFF.")
args = parser.parse_args()


# Specify the WCS endpoint url
url = 'https://wcs.geonorge.no/skwms1/wcs.hoyde-dtm-nhm-25833?service=wcs&request=getcapabilities'

# Connect to the WCS service
wcs = WebCoverageService(url, version='1.0.0')

# Specify the coverage id
coverage_id = 'nhm_dtm_topo_25833'

# Use the passed bounding box directly
bbox = (args.min_x, args.min_y, args.max_x, args.max_y)

# Calculate total width and height based on the bounding box
total_width = args.max_x - args.min_x
total_height = args.max_y - args.min_y

# The width and height of each quadrant
quadrant_width = total_width / 2
quadrant_height = total_height / 2

# Specify the workdir path
workdir_path = args.temp_dir

# List to store paths of quadrant files
quadrant_files = []

# Function to handle download and processing of a quadrant
def process_quadrant(i, j):
    # Calculate the bounding box for the quadrant
    quadrant_bbox = (
        args.min_x + i * quadrant_width,
        args.min_y + j * quadrant_height,
        args.min_x + (i + 1) * quadrant_width,
        args.min_y + (j + 1) * quadrant_height,
    )

    # Request the coverage for the quadrant
    response = wcs.getCoverage(
        identifier=coverage_id,
        bbox=quadrant_bbox,
        crs='EPSG:25833',
        format='GeoTIFF',
        resx=1,  # Adjust resolution if necessary
        resy=1
    )

    # Save the response to a GeoTIFF file
    with MemoryFile(response.read()) as memfile:
        with memfile.open() as dataset:
            quadrant_geotiff_path = os.path.join(workdir_path, f'quadrant_{i}_{j}_32b.tif')
            quadrant_files.append(quadrant_geotiff_path)
            with rasterio.open(quadrant_geotiff_path, 'w', **dataset.profile) as dst:
                dst.write(dataset.read())

# Create a ThreadPoolExecutor for parallel processing
with ThreadPoolExecutor(max_workers=4) as executor:
    # Process each quadrant
    for i in range(2):
        for j in range(2):
            executor.submit(process_quadrant, i, j)

# Prepare to merge quadrant rasters
src_files_to_mosaic = [rasterio.open(fp) for fp in quadrant_files]

# Merge quadrants
mosaic, out_trans = merge(src_files_to_mosaic)

# Update metadata for the merged raster
out_meta = src_files_to_mosaic[0].meta.copy()
out_meta.update({
    "driver": "GTiff",
    "height": mosaic.shape[1],
    "width": mosaic.shape[2],
    "transform": out_trans,
    "crs": 'EPSG:25833'
})

# Saving the merged raster
with rasterio.open(args.final_output_path, "w", **out_meta) as dest:
    dest.write(mosaic)
