from owslib.wcs import WebCoverageService
import rasterio
from rasterio.io import MemoryFile
import argparse
from rasterio.merge import merge
from concurrent.futures import ThreadPoolExecutor
import os

# Parse arguments
parser = argparse.ArgumentParser(description='Download height data for a larger area and process it into a single GeoTIFF.')
parser.add_argument("min_x", type=float, help="Minimum X coordinate of the bounding box.")
parser.add_argument("min_y", type=float, help="Minimum Y coordinate of the bounding box.")
parser.add_argument("max_x", type=float, help="Maximum X coordinate of the bounding box.")
parser.add_argument("max_y", type=float, help="Maximum Y coordinate of the bounding box.")
parser.add_argument("temp_dir", type=str, help="Temporary directory path for storing intermediate files.")
parser.add_argument("final_output_path", type=str, help="Path to save the final merged GeoTIFF.")
args = parser.parse_args()

# Constants and setup
url = 'https://wcs.geonorge.no/skwms1/wcs.hoyde-dtm-nhm-25833?service=wcs&request=getcapabilities'
coverage_id = 'nhm_dtm_topo_25833'
total_width = args.max_x - args.min_x
total_height = args.max_y - args.min_y
quadrant_width = total_width / 4
quadrant_height = total_height / 4
quadrant_files = []

# WCS service connection
wcs = WebCoverageService(url, version='1.0.0')

# Function for processing each quadrant
def process_quadrant(i, j):
    bbox = (
        args.min_x + i * quadrant_width,
        args.min_y + j * quadrant_height,
        args.min_x + (i + 1) * quadrant_width,
        args.min_y + (j + 1) * quadrant_height,
    )
    response = wcs.getCoverage(
        identifier=coverage_id,
        bbox=bbox,
        crs='EPSG:25833',
        format='GeoTIFF',
        resx=10,  # Adjusted for 1500px per quadrant
        resy=10
    )
    with MemoryFile(response.read()) as memfile:
        with memfile.open() as dataset:
            quadrant_path = os.path.join(args.temp_dir, f'quadrant_{i}_{j}_32b.tif')
            quadrant_files.append(quadrant_path)
            with rasterio.open(quadrant_path, 'w', **dataset.profile) as dst:
                dst.write(dataset.read())

# Quadrant processing with ThreadPoolExecutor
with ThreadPoolExecutor(max_workers=8) as executor:
    for i in range(4):
        for j in range(4):
            executor.submit(process_quadrant, i, j)

# Merging quadrants
src_files_to_mosaic = [rasterio.open(fp) for fp in quadrant_files]
mosaic, out_trans = merge(src_files_to_mosaic)
out_meta = src_files_to_mosaic[0].meta.copy()
out_meta.update({
    "driver": "GTiff",
    "height": mosaic.shape[1],
    "width": mosaic.shape[2],
    "transform": out_trans,
    "crs": 'EPSG:25833'
})

# Writing the mosaic raster to disk
with rasterio.open(args.final_output_path, "w", **out_meta) as dest:
    dest.write(mosaic)
