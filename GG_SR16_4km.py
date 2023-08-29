import requests
import os
from owslib.wms import WebMapService
from PIL import Image
from io import BytesIO
import rasterio
from rasterio.transform import from_origin
import numpy as np

def download_SR16_4km(center_lat, center_lon, output_location):
    try:
        print("Connecting to WMS service...")
        # Connect to the WMS service
        wms = WebMapService('https://wms.nibio.no/cgi-bin/sr16?VERSION=1.3.0&SERVICE=WMS&REQUEST=GetCapabilities')

        print("Calculating bounding box...")
        # Calculate the bounding box
        half_size = 2050  # Assuming 4km x 4km tiles and a little extra
        min_x = center_lon - half_size
        max_x = center_lon + half_size
        min_y = center_lat - half_size
        max_y = center_lat + half_size

        print("Requesting image from WMS...")
        # Request the image from the WMS
        response = wms.getmap(layers=['SRRTRESLAG'],
                              srs='EPSG:25833',
                              bbox=(min_x, min_y, max_x, max_y),
                              width=256, height=256,
                              format='image/geotiff',
                              transparent=True)
        
        print("Reading image into memory...")
        img = Image.open(BytesIO(response.read()))

        print("Converting image to NumPy array...")
        # Convert the PIL image to a NumPy array
        img_array = np.array(img)

        print("Defining CRS and geotransformation...")
        # Define the CRS
        crs = rasterio.crs.CRS.from_string("EPSG:25833")

        # Define the geotransformation
        transform = from_origin(min_x, max_y, 16, 16)  # Assuming 16m resolution

        # Define the profile (metadata)
        profile = {
            'driver': 'GTiff',
            'height': img.height,
            'width': img.width,
            'count': 1,  # Assuming a single band image
            'dtype': rasterio.uint8,
            'crs': crs,
            'transform': transform,
        }

        output_path = os.path.join(output_location, 'SR16_4km_download.tif')

        print(f"Writing GeoTIFF to {output_path}...")
        # Write the GeoTIFF
        with rasterio.open(output_path, 'w', **profile) as dst:
            dst.write(img_array, 1)

        print(f"SR16 GeoTIFF saved to {output_path}")

    except Exception as e:
        print(f"An error occurred: {e}")

# Example usage
# download_SR16_4km(6969762.280981427, 82865.59794840263, './output/')
