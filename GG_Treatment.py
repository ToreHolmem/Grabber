import platform
import subprocess
import time
import rasterio
from pyproj import CRS, Transformer
import os
from rasterio.warp import transform_bounds
import numpy as np
import imageio
from PIL import Image
import argparse
import argparse
import os
import rasterio
import numpy as np
from PIL import Image

# Parse command line arguments
parser = argparse.ArgumentParser()
parser.add_argument('center_lat', type=float)
parser.add_argument('center_lon', type=float)
parser.add_argument('output_location')
args = parser.parse_args()

# Now you can use args.output_location, args.center_lat, and args.center_lon in your script
output_location = args.output_location
center_lat = args.center_lat
center_lon = args.center_lon

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
        output_dim = max(window.width, window.height)
        profile = src.profile
        profile.update(
            width=output_dim,
            height=output_dim,
            transform=rasterio.windows.transform(window, src.transform),
            crs=epsg25833
        )
        #Debugging statement
        print(f"Profile for {output_path}: {profile}")

        with rasterio.open(output_path, 'w', **profile) as dst:
            dst.write(cropped_array)

# Function to delete all files that are not part of the final output set
def delete_files_with_download(output_dir):
    for filename in os.listdir(output_dir):
        if "download" in filename:
            file_path = os.path.join(output_dir, filename)
            try:
                os.remove(file_path)
                print(f"Deleted {filename}")
            except Exception as e:
                print(f"Error deleting {filename}: {e}")

# Function to save cropped tif files to png
def tif_to_png(tif_path, png_path):
    with rasterio.open(tif_path) as src:
        img_array = src.read()
        img_array = np.transpose(img_array, (1, 2, 0))
        if img_array.shape[2] > 3:
            img_array = img_array[:, :, :3]
        img_array = (img_array - np.min(img_array)) / (np.max(img_array) - np.min(img_array)) * 255
        imageio.imsave(png_path, img_array.astype(np.uint8))

# Function for conditional cropping
def conditional_crop_image(input_file, center_lat, center_lon, crop_size, output_file):
    if os.path.exists(input_file):
        crop_image(input_file, center_lat, center_lon, crop_size, output_file)
    else:
        print(f"File {input_file} does not exist. Skipping cropping.")

# Function for conditional PNG conversion
def conditional_tif_to_png(input_file, output_file):
    if os.path.exists(input_file):
        tif_to_png(input_file, output_file)
    else:
        print(f"File {input_file} does not exist. Skipping PNG conversion.")

# Function for converting SR16 to png and deleting tiff file
def tif_to_custom_rgb_png_and_delete(tif_path, png_path):
    if os.path.exists(tif_path):
        with rasterio.open(tif_path) as src:
            img_array = src.read(1)  # Reading the first band

            # Create a mask for nodata values
            nodata_mask = (img_array == src.nodatavals[0])

            # Create an empty RGB image with a black border
            rgb_array = np.zeros((img_array.shape[0] + 2, img_array.shape[1] + 2, 3), dtype=np.uint8)
            rgb_array[1:-1, 1:-1] = 255  # Set the interior pixels to white

            # Fill the R, G, B channels based on the actual pixel values
            rgb_array[1:-1, 1:-1, 0] = np.where(img_array == 3, 255, 0)  # Red channel
            rgb_array[1:-1, 1:-1, 1] = np.where(img_array == 2, 255, 0)  # Green channel
            rgb_array[1:-1, 1:-1, 2] = np.where(img_array == 1, 255, 0)  # Blue channel

            # Apply the nodata mask to all channels
            rgb_array[1:-1, 1:-1, 0][nodata_mask] = 0  # Red channel
            rgb_array[1:-1, 1:-1, 1][nodata_mask] = 0  # Green channel
            rgb_array[1:-1, 1:-1, 2][nodata_mask] = 0  # Blue channel

            # Debugging
            print(f"Shape of rgb_array: {rgb_array.shape}")
            print(f"Data type of rgb_array: {rgb_array.dtype}")

            # Create an image from the numpy array
            try:
                img_pil = Image.fromarray(rgb_array, 'RGB')
                img_pil.save(png_path)
            except ValueError as e:
                print(f"An error occurred: {e}")
                return
    else:
        print(f"File {tif_path} does not exist. Skipping operation.")

    # Delete the intermediate TIFF file
    try:
        os.remove(tif_path)
        print(f"Deleted {tif_path}")
    except Exception as e:
        print(f"Error deleting {tif_path}: {e}")

print("Cropping Files")

#Crop images to the same area - 1km - 1009 meters to match Unreal Engine landscape preferences
crop_size_meters = 1009
#conditional_crop_image(os.path.join(output_location, 'height_1km_download.tif'), center_lat, center_lon, crop_size_meters, os.path.join(output_location, 'height_1km.tiff'))
conditional_crop_image(os.path.join(output_location, 'aerial_1km_download.tif'), center_lat, center_lon, crop_size_meters, os.path.join(output_location, 'aerial_1km.tiff'))

#Crop images to the same area - 4km - 4033 meters to match Unreal Engine landscape preferences
crop_size_meters_4km = 4033
conditional_crop_image(os.path.join(output_location, 'aerial_4km_download.tif'), center_lat, center_lon, crop_size_meters_4km, os.path.join(output_location, 'aerial_4km.tiff'))
conditional_crop_image(os.path.join(output_location, 'height_4km_download.tif'), center_lat, center_lon, crop_size_meters_4km, os.path.join(output_location, 'height_4km.tiff'))

# Crop the existing SR16 geotiff to the same 4km area
conditional_crop_image(os.path.join(output_location, 'sr16_15_SRRTRESLAG.tif'), center_lat, center_lon, crop_size_meters_4km, os.path.join(output_location, 'sr16_15_SRRTRESLAG_4km_download.tiff'))

print("Saving images as PNG copies")

#Convert the aerial images to PNGs as well
conditional_tif_to_png(os.path.join(output_location, 'aerial_1km.tiff'), os.path.join(output_location, 'aerial_1km_copy.png'))
conditional_tif_to_png(os.path.join(output_location, 'aerial_4km.tiff'), os.path.join(output_location, 'aerial_4km_copy.png'))

# Convert SR16 to PNG
tif_path = os.path.join(output_location, 'sr16_15_SRRTRESLAG_4km_download.tiff')
png_path = os.path.join(output_location, 'SR16_4km_Alpha.png')
tif_to_custom_rgb_png_and_delete(tif_path, png_path)

print("Deleting files")
def delete_files_with_download(output_location):
    # Get a list of all files in the output directory
    files = os.listdir(output_location)
    
    # Iterate over the files and delete any file that contains the word "download" in its name
    for file in files:
        if "download" in file:
            file_path = os.path.join(output_location, file)
            os.remove(file_path)

delete_files_with_download(output_location)