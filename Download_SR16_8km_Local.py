import rasterio
import argparse
from pyproj import Transformer

# Hard-coded GeoTIFF location
geotiff_location = "X:/Dropbox/! Prosjekter/GEOS/01 Assets/! Data/SR16 MR/sr16_15_SRRTRESLAG.tif"

# Parse command line arguments
parser = argparse.ArgumentParser()
parser.add_argument("center_lat", type=float, help="Center latitude")
parser.add_argument("center_lon", type=float, help="Center longitude")
parser.add_argument("output_location", type=str, help="Output location")
args = parser.parse_args()

def process_geotiff(geotiff_location, output_location, center_lat, center_lon):
    try:
        print("Opening GeoTIFF file...")
        with rasterio.open(geotiff_location) as src:
            print("Calculating bounding box...")
            min_x, min_y, max_x, max_y = src.bounds

            # Create a transformer to convert from geographic coordinates to the GeoTIFF file's coordinate system
            transformer = Transformer.from_crs("EPSG:4326", "EPSG:25833", always_xy=True)

            # Convert the center latitude and longitude to the GeoTIFF file's coordinate system
            center_x, center_y = transformer.transform(center_lon, center_lat)

            # Define the bounding box of the area you want to crop
            # Here, I'm using the center_x and center_y to define a 1x1 degree box
            # Note: You might need to adjust the size of the box depending on the units of the GeoTIFF file's coordinate system
            crop_min_x = center_x - 4000
            crop_min_y = center_y - 4000
            crop_max_x = center_x + 4000
            crop_max_y = center_y + 4000

            # Create a window from the bounding box
            window = rasterio.windows.from_bounds(crop_min_x, crop_min_y, crop_max_x, crop_max_y, src.transform)

            print(f"Cropping to: ({crop_min_x}, {crop_min_y}, {crop_max_x}, {crop_max_y})")
            print("Spatial reference system: EPSG:25833")

            print("Saving image...")
            output_file = f"{output_location}/sr16_15_SRRTRESLAG_4km_download.tiff"
            with rasterio.open(output_file, 'w', driver='GTiff', height=window.height, width=window.width, count=1, dtype=src.dtypes[0], crs=src.crs, transform=src.window_transform(window)) as dst:
                dst.write(src.read(1, window=window), 1)

            print("Image saved successfully.")

    except Exception as e:
        print(f"An error occurred: {e}")

# Use hard-coded geotiff_location and command line argument for output_location
process_geotiff(geotiff_location, args.output_location, args.center_lat, args.center_lon)