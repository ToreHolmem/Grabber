import os
import glob
from pyproj import Proj, transform
from owslib.wcs import WebCoverageService

# Convert from EPSG:4326 to EPSG:25833
def convert_coords(lat, lon):
    in_proj = Proj(init='epsg:4326')
    out_proj = Proj(init='epsg:25833')
    x, y = transform(in_proj, out_proj, lon, lat)
    return x, y

# Get an incremental file name
def get_output_filename(output_dir, base_name):
    existing_files = glob.glob(os.path.join(output_dir, f"{base_name}_*.tif"))
    max_number = 0
    for file in existing_files:
        number = int(os.path.basename(file)[len(base_name) + 1:-4])
        if number > max_number:
            max_number = number
    return os.path.join(output_dir, f"{base_name}_{max_number + 1:04}.tif")

# Connect to the WCS service
wcs = WebCoverageService('https://wcs.geonorge.no/skwms1/wcs.hoyde-dtm-nhm-25833?', version='2.0.1')

# Choose the layer you are interested in
layer = 'nhm_dtm_topo_25833'

# Define the output format
format = 'image/GeoTIFF'

# Define the center of the bounding box
center_lat = 62.45420359364632
center_lon = 7.668951948534192

# Convert the center coordinates to EPSG:25833
center_x, center_y = convert_coords(center_lat, center_lon)

# Define the size of the bounding box (1 km square)
size = 1000  # in meters

# Compute the bounding box (minx, miny, maxx, maxy)
bbox = (center_x - size/2, center_y - size/2, center_x + size/2, center_y + size/2)

# Define the CRS
crs = 'urn:ogc:def:crs:EPSG::25833'

# Define the interpolation type
interpolation = 'linear'

# Get the data
response = wcs.getCoverage(identifier=[layer], format=format, bbox=bbox, crs=crs, interpolation=interpolation)

# Get an output filename
output_dir = '../Output'
base_name = 'Height_WCS'
filename = get_output_filename(output_dir, base_name)

# Save the data to a file
with open(filename, 'wb') as file:
    file.write(response.read())
