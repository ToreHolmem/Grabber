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
    with rasterio.open(tif_path) as src:
        img_array = src.read(1)  # Reading the first band

        # Create a mask for nodata values
        nodata_mask = (img_array == src.nodatavals[0])

        # Create an empty RGB image
        rgb_array = np.zeros((img_array.shape[0], img_array.shape[1], 3), dtype=np.uint8)

        # Fill the R, G, B channels based on the actual pixel values
        rgb_array[:,:,0] = np.where(img_array == 3, 255, 0)  # Red channel gets the pixels with value 3
        rgb_array[:,:,1] = np.where(img_array == 2, 255, 0)  # Green channel gets the pixels with value 2
        rgb_array[:,:,2] = np.where(img_array == 1, 255, 0)  # Blue channel gets the pixels with value 1

        # Apply the nodata mask to all channels
        rgb_array[nodata_mask] = 0

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

    # Delete the intermediate TIFF file
    try:
        os.remove(tif_path)
        print(f"Deleted {tif_path}")
    except Exception as e:
        print(f"Error deleting {tif_path}: {e}")

    # Delete the intermediate TIFF file
    try:
        os.remove(tif_path)
        print(f"Deleted {tif_path}")
    except Exception as e:
        print(f"Error deleting {tif_path}: {e}")


center_lat = 62.62104190802922
center_lon = 6.854110293340546

if platform.system() == 'Windows':
    output_location = r"X:\Dropbox\! Prosjekter\Fiksdal\03 Assets\Data\Python Scripts Output"
else:
    output_location = "/Users/toreholmem/Dropbox/! Prosjekter/Fiksdal/03 Assets/Data/Python Scripts Output"

scripts_to_run = [
    #'GG_Aerial_1km.py',
    #'GG_Aerial_4km.py',
    #'GG_Height_1km.py',
    #'GG_Height_4km.py',
    #'GG_Height_60km.py',
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

#Crop images to the same area - 1km - 1009 meters to match Unreal Engine landscape preferences
crop_size_meters = 1009
conditional_crop_image(os.path.join(output_location, 'height_1km_download.tif'), center_lat, center_lon, crop_size_meters, os.path.join(output_location, 'height_1km.tiff'))
conditional_crop_image(os.path.join(output_location, 'aerial_1km_download.tif'), center_lat, center_lon, crop_size_meters, os.path.join(output_location, 'aerial_1km.tiff'))

#Crop images to the same area - 4km - 4033 meters to match Unreal Engine landscape preferences
crop_size_meters_4km = 4033
conditional_crop_image(os.path.join(output_location, 'aerial_4km_download.tif'), center_lat, center_lon, crop_size_meters_4km, os.path.join(output_location, 'aerial_4km.tiff'))
conditional_crop_image(os.path.join(output_location, 'height_4km_download.tif'), center_lat, center_lon, crop_size_meters_4km, os.path.join(output_location, 'height_4km.tiff'))

# Crop the existing SR16 geotiff to the same 4km area
conditional_crop_image(os.path.join(output_location, 'sr16_15_SRRTRESLAG.tif'), center_lat, center_lon, crop_size_meters_4km, os.path.join(output_location, 'sr16_15_SRRTRESLAG_4km_download.tiff'))

print("Saving images as PNG copies")

#Convert the aerial images to PNGs as well
#conditional_tif_to_png(os.path.join(output_location, 'aerial_1km.tiff'), os.path.join(output_location, 'aerial_1km_copy.png'))
#conditional_tif_to_png(os.path.join(output_location, 'aerial_4km.tiff'), os.path.join(output_location, 'aerial_4km_copy.png'))

# Convert SR16 to PNG
tif_path = os.path.join(output_location, 'sr16_15_SRRTRESLAG_4km_download.tiff')
png_path = os.path.join(output_location, 'SR16_4km_Alpha.png')
tif_to_custom_rgb_png_and_delete(tif_path, png_path)

#Clean up
print("Cleaning up")
delete_files_with_download(output_location)

#print("All files downloaded and cropped great script good job thumbsup")