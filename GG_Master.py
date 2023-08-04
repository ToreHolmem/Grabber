import platform
import subprocess
import time
import rasterio
from pyproj import CRS, Transformer
import os


# Define your variables
center_lat = 62.62104190802922
center_lon = 6.854110293340546

# Detect the operating system and use the correct path format
if platform.system() == 'Windows':
    output_location = r"X:\Dropbox\! Prosjekter\Fiksdal\03 Assets\Data\Python Scripts Output"
else:
    output_location = "/Users/toreholmem/Dropbox/! Prosjekter/Fiksdal/03 Assets/Data/Fra GGrabber"

scripts_to_run = [
    #GG_Aerial_1km.py',
    #'GG_Aerial_1km_GN.py'
    #GG_Aerial_1km_NIB.py'
    #'GG_Aerial_1km_V2.py'
    #'GG_Aerial_1km_Rasterio.py'
    #'GG_Aerial_4km.py',
    #'GG_Aerial_60km.py',
    'GG_Height_1km.py',
    #'GG_Height_4km.py',
    #'GG_Height_60km.py'
    #'Query dump.py'
]

for script in scripts_to_run:
    print(f'Starting {script}...')
    start_time = time.time()
    process = subprocess.Popen(['python', script, str(center_lat), str(center_lon), output_location], stdout=subprocess.PIPE)
    while True:
        output = process.stdout.readline()
        if process.poll() is not None:
            break
        if output:
            print(output.strip().decode('utf-8'))
    end_time = time.time()
    print(f'Finished {script} in {end_time - start_time} seconds.\n')

print("All scripts executed.")

# Function to crop the image
def crop_image(file_path, center_lat, center_lon, size_meters, output_path):
    # Define the coordinate systems
    wgs84 = CRS('EPSG:4326')  # WGS84
    epsg32633 = CRS('EPSG:32633')  # UTM zone 33N

    # Define the transformer
    transformer = Transformer.from_crs(wgs84, epsg32633)

    # Convert center point to EPSG:32633
    center_x, center_y = transformer.transform(center_lat, center_lon)

    # Calculate the bounding box (minx, miny, maxx, maxy)
    half_size = size_meters / 2
    bbox = (
        center_x - half_size,  # minx
        center_y - half_size,  # miny
        center_x + half_size,  # maxx
        center_y + half_size,  # maxy
    )

    with rasterio.open(file_path) as src:
        # Calculate the window that corresponds to the bounding box
        window = rasterio.windows.from_bounds(*bbox, transform=src.transform)

        # Read the pixel values from the window
        cropped_array = src.read(window=window)

        # Update the profile with the new shape
        profile = src.profile
        profile.update(
            width=window.width,
            height=window.height,
            transform=rasterio.windows.transform(window, src.transform),
        )

        # Write the cropped image to a new file
        with rasterio.open(output_path, 'w', **profile) as dst:
            dst.write(cropped_array)


# Crop the height and aerial images
crop_size_meters = 1009
crop_image(os.path.join(output_location, 'height_1km_download.tif'), center_lat, center_lon, crop_size_meters, os.path.join(output_location, 'height_1km_cropped.tif'))
crop_image(os.path.join(output_location, 'aerial_1km_download.tif'), center_lat, center_lon, crop_size_meters, os.path.join(output_location, 'aerial_1km_cropped.tif'))

print("Cropping completed.")