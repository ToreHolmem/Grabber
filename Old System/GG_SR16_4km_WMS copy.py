import requests
from owslib.wms import WebMapService
from PIL import Image
from io import BytesIO
import rasterio
from rasterio.transform import from_origin

def download_SR16_4km(center_lat, center_lon, output_location):
    try:
        print("Connecting to WMS service...")
        wms = WebMapService('https://wms.nibio.no/cgi-bin/sr16?VERSION=1.3.0&SERVICE=WMS&REQUEST=GetCapabilities')

        print("Calculating bounding box...")
        half_size = 2050
        min_x = center_lon - half_size
        max_x = center_lon + half_size
        min_y = center_lat - half_size
        max_y = center_lat + half_size

        print("Requesting image from WMS...")
        img = wms.getmap(layers=['SRRTRESLAG'],
                         srs='EPSG:25833',
                         bbox=(min_x, min_y, max_x, max_y),
                         size=(256, 256),
                         format='image/tiff')

        print("Saving image...")
        with open(output_location, 'wb') as out:
            out.write(img.read())

        print("Image saved successfully.")

    except Exception as e:
        print(f"An error occurred: {e}")

# Example usage
download_SR16_4km(60.4720, 8.4689, 'output.tif')