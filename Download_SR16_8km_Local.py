import rasterio
import argparse
from rasterio.windows import from_bounds

# Parse arguments
# Updated argparse to include temp_dir and final_output_path
parser = argparse.ArgumentParser(description="Download aerial imagery data for a specific bounding box.")
parser.add_argument("min_x", type=float, help="Minimum X coordinate of the bounding box.")
parser.add_argument("min_y", type=float, help="Minimum Y coordinate of the bounding box.")
parser.add_argument("max_x", type=float, help="Maximum X coordinate of the bounding box.")
parser.add_argument("max_y", type=float, help="Maximum Y coordinate of the bounding box.")
parser.add_argument("temp_dir", type=str, help="Temporary directory path for storing intermediate files.")
parser.add_argument("final_output_path", type=str, help="Path to save the final stitched image.")
args = parser.parse_args()

geotiff_location = "X:/Dropbox/! Prosjekter/GEOS/01 Assets/! Data/SR16 MR/sr16_15_SRRTRESLAG.tif"

def process_geotiff(geotiff_location, final_output_path, min_x, min_y, max_x, max_y):
    try:
        print("Opening GeoTIFF file...")
        with rasterio.open(geotiff_location) as src:
            print(f"Cropping to: ({min_x}, {min_y}, {max_x}, {max_y})")
            window = from_bounds(min_x, min_y, max_x, max_y, src.transform)

            print("Saving cropped image to:", final_output_path)
            with rasterio.open(final_output_path, 'w', driver='GTiff',
                               height=window.height, width=window.width,
                               count=src.count, dtype=src.dtypes[0],
                               crs=src.crs, transform=src.window_transform(window)) as dst:
                dst.write(src.read(window=window))

            print("Cropped image saved successfully.")

    except Exception as e:
        print(f"An error occurred: {e}")

# Assuming 'geotiff_location' is defined earlier in the script or loaded from parameters
process_geotiff(geotiff_location, args.final_output_path, args.min_x, args.min_y, args.max_x, args.max_y)