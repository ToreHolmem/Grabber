import GG_Script_Runner as script_runner
import json
import subprocess
import pyproj
from pyproj import Transformer
import os
import tempfile
import time
import rasterio
from rasterio.crs import CRS
from rasterio.windows import from_bounds as window_from_bounds
from rasterio.warp import transform_bounds
from math import cos, pi

# This script is called "GG_Main.py" and is used to run the various scripts for downloading and processing geospatial data.

# Run GG_Parameters.py to update the JSON file
print("Running GG_Parameters v4 - UI.py")
subprocess.run(["python", "GG_Parameters v4 - UI.py"], check=True)
print("Parameters updated")

# Load parameters from a JSON file
print("Loading parameters from JSON")
with open('parameters.json', 'r') as f:
    parameters = json.load(f)

# Extract script configurations from the loaded parameters
script_configs = parameters['scripts']

def calculate_bounding_box(center_lat, center_lon, half_size_m):
    # Assume half_size_m is already in meters, so no conversion is needed

    # Calculate the bounding box in geographic coordinates (WGS84)
    min_x = center_lon - half_size_m / (111.32 * 1000 * cos(center_lat * pi / 180))
    max_x = center_lon + half_size_m / (111.32 * 1000 * cos(center_lat * pi / 180))
    min_y = center_lat - half_size_m / (111.32 * 1000)
    max_y = center_lat + half_size_m / (111.32 * 1000)
    bbox_wgs84 = (min_x, min_y, max_x, max_y)
    
    # Transform the bounding box to the target CRS (EPSG:25833)
    transformer = pyproj.Transformer.from_crs("epsg:4326", "epsg:25833", always_xy=True)
    min_x, min_y = transformer.transform(bbox_wgs84[0], bbox_wgs84[1])
    max_x, max_y = transformer.transform(bbox_wgs84[2], bbox_wgs84[3])
    bbox_utm = (min_x, min_y, max_x, max_y)
    
    return bbox_utm


print("Bounding box calculation function defined")

scripts_to_run = list(script_configs.keys())

# Create a temporary directory for intermediate files
with tempfile.TemporaryDirectory() as tempdir:
    print("Using temporary directory for intermediate files:", tempdir)
    
    for script_name in scripts_to_run:
        config = script_configs[script_name]

        # Check if the script should be executed
        if config.get("execute"):  # This checks if the 'execute' key exists and if it is True
            bbox_utm = calculate_bounding_box(parameters["center_lat"], parameters["center_lon"], config["bbox_size_km_download"] / 2)
            output_file_name = config["output_file_name"]
            final_output_path = os.path.join(parameters['output_location'], output_file_name)

            print(f"Bounding Box for {script_name} in UTM (EPSG:25833): {bbox_utm}")
            
            subprocess.run(["python", script_name, str(bbox_utm[0]), str(bbox_utm[1]), str(bbox_utm[2]), str(bbox_utm[3]), tempdir, final_output_path], check=True)
        else:
            print(f"Skipping execution of {script_name} as per configuration.")

    print("All scripts executed successfully")

print("Starting cropping process")

# Use the global center coordinates
center_lon = parameters['center_lon']
center_lat = parameters['center_lat']

# Updated cropping function
def crop_image(file_path, center_lat, center_lon, size_meters, output_path):
    wgs84 = CRS.from_epsg(4326)  # WGS84
    epsg25833 = CRS.from_epsg(25833)  # UTM zone 33N
    transformer = Transformer.from_crs(wgs84, epsg25833, always_xy=True)
    center_x, center_y = transformer.transform(center_lon, center_lat)  # Note the order of lon, lat for always_xy=True
    half_size = size_meters / 2
    bbox = (
        center_x - half_size,  # minx
        center_y - half_size,  # miny
        center_x + half_size,  # maxx
        center_y + half_size   # maxy
    )
    with rasterio.open(file_path) as src:
        if src.crs != epsg25833:
            bbox = transform_bounds(wgs84, epsg25833, *bbox, always_xy=True)
        window = window_from_bounds(*bbox, transform=src.transform)
        cropped_array = src.read(window=window)
        output_dim = max(window.width, window.height)
        profile = src.profile
        profile.update(
            width=output_dim,
            height=output_dim,
            transform=rasterio.windows.transform(window, src.transform),
            crs=epsg25833
        )
        print(f"Profile for {output_path}: {profile}")  # Debugging statement

        with rasterio.open(output_path, 'w', **profile) as dst:
            dst.write(cropped_array)

# Cropping process based on parameters.json
for script_name, config in parameters['scripts'].items():
    if config.get("crop"):  # Checks if the 'crop' key exists and if it is True
        geotiff_path = os.path.join(parameters['output_location'], config['output_file_name'])
        side_length_meters = config['bbox_size_km_crop'] * 1  # Remnant, to be removed in future versions. Data is in meters already.
        output_path = os.path.join(parameters['output_location'], config['cropped_file_name'])
        crop_image(geotiff_path, parameters['center_lat'], parameters['center_lon'], side_length_meters, output_path)
        print(f"Finished cropping {script_name}")
    else:
        print(f"Skipping cropping for {script_name} as per configuration.")

# Deleting temp files with _DL in name

def delete_dl_files(output_location):
    for filename in os.listdir(output_location):
        if '_DL' in filename:
            file_path = os.path.join(output_location, filename)
            try:
                os.remove(file_path)
                print(f"Deleted: {filename}")
            except Exception as e:
                print(f"Error deleting file {filename}: {e}")

# After all processing is done, call the function with the output location
print("Deleting temporary _DL files")
delete_dl_files(parameters['output_location'])

print("All done, good job! Geos rules!")