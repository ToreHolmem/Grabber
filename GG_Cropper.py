import rasterio
from rasterio.windows import Window
from rasterio.transform import from_origin
import os
import sys  # For accessing command-line arguments

# This script is called "GG_Cropper.py" and is used to crop a GeoTIFF file based on a center coordinate and side length.

# Check if the correct number of arguments are passed
if len(sys.argv) != 6:  # Adjusted to expect 6 items, including the script name
    print("Usage: python GG_Cropper.py <path_to_geotiff> <center_lon> <center_lat> <side_length_meters> <output_path>")
    sys.exit(1)

# Assigning command-line arguments to variables
geotiff_path = sys.argv[1]
center_lon = float(sys.argv[2])
center_lat = float(sys.argv[3])
side_length_meters = float(sys.argv[4])
output_path = sys.argv[5]

# Open the GeoTIFF file
with rasterio.open(geotiff_path) as src:
    # Convert center geospatial coordinate to pixel coordinates
    center_x, center_y = src.index(center_lon, center_lat)
    
    # Calculate pixel size in meters
    pixel_size_x, pixel_size_y = src.res
    
    # Calculate the number of pixels needed to cover the desired square bounding box
    pixels_across = side_length_meters / pixel_size_x
    pixels_down = side_length_meters / abs(pixel_size_y)  # Pixel size can be negative
    
    # Calculate the offsets for the window
    offset_x = center_x - (pixels_across / 2)
    offset_y = center_y - (pixels_down / 2)
    
    # Define the window to crop
    window = Window(offset_x, offset_y, pixels_across, pixels_down)
    
    # Read the data in the window
    data = src.read(window=window)
    
    # Update the metadata for the output file
    out_meta = src.meta.copy()
    out_meta.update({
        "driver": "GTiff",
        "height": int(pixels_down),
        "width": int(pixels_across),
        "transform": rasterio.windows.transform(window, src.transform)
    })
    
    # Write the cropped image
    with rasterio.open(output_path, "w", **out_meta) as dest:
        dest.write(data)

print(f"Cropped GeoTIFF saved to {output_path}")
