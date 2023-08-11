import platform
import subprocess
import time
import rasterio
from pyproj import CRS, Transformer
import os
from rasterio.warp import transform_bounds

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


center_lat = 62.62104190802922
center_lon = 6.854110293340546

if platform.system() == 'Windows':
    output_location = r"X:\Dropbox\! Prosjekter\Fiksdal\03 Assets\Data\Python Scripts Output\V002"
else:
    output_location = "/Users/toreholmem/Dropbox/! Prosjekter/Fiksdal/03 Assets/Data/Fra GGrabber"

scripts_to_run = [
    'GG_Aerial_1km.py',
    'GG_Aerial_4km.py',
    'GG_Height_1km.py',
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

crop_size_meters = 1000
crop_image(os.path.join(output_location, 'height_1km_download.tif'), center_lat, center_lon, crop_size_meters, os.path.join(output_location, 'height_1km_cropped.tif'))
crop_image(os.path.join(output_location, 'aerial_1km_download.tif'), center_lat, center_lon, crop_size_meters, os.path.join(output_location, 'aerial_1km_cropped.tif'))

crop_size_meters_4km = 4000
crop_image(os.path.join(output_location, 'aerial_4km_download.tif'), center_lat, center_lon, crop_size_meters_4km, os.path.join(output_location, 'aerial_4km_cropped.tif'))

print("Cropping completed.")

