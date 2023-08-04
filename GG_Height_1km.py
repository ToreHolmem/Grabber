from owslib.wcs import WebCoverageService
import rasterio
from pyproj import CRS, Transformer
import argparse
import os
from rasterio.io import MemoryFile

# Parse arguments
parser = argparse.ArgumentParser()
parser.add_argument("center_lat", type=float)
parser.add_argument("center_lon", type=float)
parser.add_argument("output_location", type=str)
args = parser.parse_args()

# Specify the WCS endpoint url
url = 'https://wcs.geonorge.no/skwms1/wcs.hoyde-dtm-nhm-25833?service=wcs&request=getcapabilities'

# Connect to the WCS service
wcs = WebCoverageService(url, version='1.0.0')

# Center point (latitude, longitude)
center_lat, center_lon = args.center_lat, args.center_lon

# Define the coordinate systems
wgs84 = CRS('EPSG:4326')  # WGS84
epsg32633 = CRS('EPSG:32633')  # UTM zone 33N (changed from 25833)

# Define the transformer
transformer = Transformer.from_crs(wgs84, epsg32633)  # changed to 32633

# Convert center point to EPSG:32633
center_x, center_y = transformer.transform(center_lat, center_lon)

# Calculate the bounding box (minx, miny, maxx, maxy)
bbox = (
    center_x - 600,  # minx
    center_y - 600,  # miny
    center_x + 600,  # maxx
    center_y + 600,  # maxy
)

# Request the coverage
response = wcs.getCoverage(
    identifier='nhm_dtm_topo_25833',
    bbox=bbox,
    crs='EPSG:32633',  # changed to 32633
    format='GeoTIFF',
    resx=1,
    resy=1
)

# Save the response to a GeoTIFF file
with MemoryFile(response.read()) as memfile:
    with memfile.open() as dataset:
        data = dataset.read() # Read the data while the dataset is still open

        original_geotiff_path = os.path.join(args.output_location, 'height_1km_download.tif')
        with rasterio.open(original_geotiff_path, 'w', **dataset.profile) as original_dst:
            original_dst.write(data) # Write the data to the new GeoTIFF

print("Height GeoTIFF Information:")
print(f"  CRS: {dataset.crs}")
print(f"  Transform: {dataset.transform}")
print(f"  Width: {dataset.width}, Height: {dataset.height}")
print(f"  Pixel Size: {dataset.res[0]} meters, {dataset.res[1]} meters")


print(f"GeoTIFF saved to {original_geotiff_path}")

original_geotiff_path = os.path.join(args.output_location, 'height_1km_download.tif')
with rasterio.open(original_geotiff_path, 'w', **dataset.profile) as original_dst:
    original_dst.write(dataset.read())


