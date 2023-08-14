import platform
import subprocess
import time
import rasterio
from pyproj import CRS, Transformer
import os
from rasterio.warp import transform_bounds
import numpy as np
import imageio

# Function to crop the image
def crop_image(file_path, center_lat, center_lon, size_meters, output_path):
    wgs84 = CRS('EPSG:4326')  # WGS84
    epsg25833 = CRS('EPSG:25833')  # UTM zone 33N
    transformer = Transformer.from_crs(wgs84, epsg25833)

    center_x, center_y = transformer.transform(center_lat, center_lon)

    half_size = size_meters / 2

    bbox = (
        center_x - half_size,  # minx
        center_y - half_size,  # miny
        center_x + half_size,  # maxx
        center_y + half_size   # maxy
    )

    with rasterio.open(file_path) as src:
        if src.crs != epsg25833:
            bbox = transform_bounds(src.crs, epsg25833, *bbox)

        window = rasterio.windows.from_bounds(*bbox, transform=src.transform)
        cropped_array = src.read(window=window)

        # Assuming you want the output to be square and the number of pixels
        # to match the largest dimension of the window.
        output_dim = max(window.width, window.height)

        profile = src.profile
        profile.update(
            width=output_dim,
            height=output_dim,
            transform=rasterio.windows.transform(window, src.transform),
            crs=epsg25833
        )

        with rasterio.open(output_path, 'w', **profile) as dst:
            dst.write(cropped_array)

# Function to delete all files that are not part of the final output set
def delete_files_with_download(output_dir):
    # Loop through all files in the directory
    for filename in os.listdir(output_dir):
        # Check if "download" is in the filename
        if "download" in filename:
            # Construct full file path
            file_path = os.path.join(output_dir, filename)
            try:
                # Remove the file
                os.remove(file_path)
                print(f"Deleted {filename}")
            except Exception as e:
                print(f"Error deleting {filename}: {e}")

#Function to save cropped tif files to png
def tif_to_png(tif_path, png_path):
    with rasterio.open(tif_path) as src:
        img_array = src.read()
        img_array = np.transpose(img_array, (1, 2, 0))  # This reorders the dimensions from (bands, height, width) to (height, width, bands)
        
        # Ensure there's no more than 3 bands (R, G, B) for PNG.
        if img_array.shape[2] > 3:
            img_array = img_array[:, :, :3]

        # Normalize to 0-255 if the image isn't already in that range
        img_array = (img_array - np.min(img_array)) / (np.max(img_array) - np.min(img_array)) * 255
        
        imageio.imsave(png_path, img_array.astype(np.uint8))

center_lat = 62.62104190802922
center_lon = 6.854110293340546

if platform.system() == 'Windows':
    output_location = r"X:\Dropbox\! Prosjekter\Fiksdal\03 Assets\Data\Python Scripts Output"
else:
    output_location = "/Users/toreholmem/Dropbox/! Prosjekter/Fiksdal/03 Assets/Data/Python Scripts Output"

scripts_to_run = [
    'GG_Aerial_1km.py',
    'GG_Aerial_4km.py',
    'GG_Height_1km.py',
    'GG_Height_4km.py',
    'GG_Height_60km.py',
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

print("Cropping Files")

#Crop images to the same area - 1km
crop_size_meters = 1009
crop_image(os.path.join(output_location, 'height_1km_download.tif'), center_lat, center_lon, crop_size_meters, os.path.join(output_location, 'height_1km.tif'))
crop_image(os.path.join(output_location, 'aerial_1km_download.tif'), center_lat, center_lon, crop_size_meters, os.path.join(output_location, 'aerial_1km.tif'))

#Crop images to the same area - 4km
crop_size_meters_4km = 4033
crop_image(os.path.join(output_location, 'aerial_4km_download.tif'), center_lat, center_lon, crop_size_meters_4km, os.path.join(output_location, 'aerial_4km.tif'))
crop_image(os.path.join(output_location, 'height_4km_download.tif'), center_lat, center_lon, crop_size_meters_4km, os.path.join(output_location, 'height_4km.tif'))

print("Saving Aerial images as PNG copies")

#Convert the aerial images to PNGs as well
tif_to_png(os.path.join(output_location, 'aerial_1km.tif'), os.path.join(output_location, 'aerial_1km_copy.png'))
tif_to_png(os.path.join(output_location, 'aerial_4km.tif'), os.path.join(output_location, 'aerial_4km_copy.png'))

#Clean up
print("Cleaning up")
delete_files_with_download(output_location)

#print("All files downloaded and cropped")

