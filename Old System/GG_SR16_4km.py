import rasterio
from rasterio.windows import from_bounds
import numpy as np
import sys

center_lat = float(sys.argv[1])
center_lon = float(sys.argv[2])
output_location = sys.argv[3]

def extract_SR16_4km(center_lat, center_lon, output_location):
    print("Opening local GeoTIFF file...")
    with rasterio.open('X:/Dropbox/! Prosjekter/GEOS/01 Assets/! Data/SR16 MR/sr16_15_SRRTRESLAG.tif') as src:
        print("Calculating bounding box...")
        half_size = 2050  # Assuming 4km x 4km tiles and a little extra
        min_x = center_lon - half_size
        max_x = center_lon + half_size
        min_y = center_lat - half_size
        max_y = center_lat + half_size

        print("Extracting subset from GeoTIFF...")
        window = from_bounds(min_x, min_y, max_x, max_y, src.transform)
        subset = src.read(window=window)

        print("Saving subset to output location...")
        meta = src.meta.copy()
        meta.update({
            'height': subset.shape[1],
            'width': subset.shape[2],
            'transform': rasterio.windows.transform(window, src.transform)})
        with rasterio.open(output_location, 'w', **meta) as dst:
            dst.write(subset)

# Call the function
extract_SR16_4km(center_lat, center_lon, output_location)