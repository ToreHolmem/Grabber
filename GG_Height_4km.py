from owslib.wcs import WebCoverageService
import rasterio
from pyproj import CRS, Transformer
import argparse
import os
from rasterio.io import MemoryFile
from rasterio import merge

# Define a function to compute the bounding box for each segment
def get_segment_bbox(center_x, center_y, segment_size, segment):
    offsets = {
        "NW1": (-2*segment_size, 2*segment_size),
        "NW2": (-segment_size, 2*segment_size),
        "NW3": (-2*segment_size, segment_size),
        "NW4": (-segment_size, segment_size),
        
        "NE1": (0, 2*segment_size),
        "NE2": (segment_size, 2*segment_size),
        "NE3": (0, segment_size),
        "NE4": (segment_size, segment_size),
        
        "SW1": (-2*segment_size, 0),
        "SW2": (-segment_size, 0),
        "SW3": (-2*segment_size, -segment_size),
        "SW4": (-segment_size, -segment_size),
        
        "SE1": (0, 0),
        "SE2": (segment_size, 0),
        "SE3": (0, -segment_size),
        "SE4": (segment_size, -segment_size)
    }
    offset_x, offset_y = offsets[segment]
    return (
        center_x + offset_x,
        center_y + offset_y,
        center_x + offset_x + segment_size,
        center_y + offset_y + segment_size
    )

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
epsg25833 = CRS('EPSG:25833')  # UTM zone 33N

# Define the transformer
transformer = Transformer.from_crs(wgs84, epsg25833)

# Convert center point to EPSG:25833
center_x, center_y = transformer.transform(center_lat, center_lon)

# Segment size
segment_size = 1000  # 2km is now split into two

segments = ["NW1", "NW2", "NW3", "NW4", 
            "NE1", "NE2", "NE3", "NE4", 
            "SW1", "SW2", "SW3", "SW4", 
            "SE1", "SE2", "SE3", "SE4"]

datasets = []

for segment in segments:
    print(f"Downloading segment: {segment}")
    
    # Calculate the bounding box for the segment
    bbox = get_segment_bbox(center_x, center_y, segment_size, segment)

    # Request the coverage for the segment
    response = wcs.getCoverage(
        identifier='nhm_dtm_topo_25833',
        bbox=bbox,
        crs='EPSG:25833',
        format='GeoTIFF',
        resx=1,
        resy=1
    )

    # Diagnostic: Save the content of a specific segment to a file
    if segment == "SE4":
        with open("diagnostic_se4_segment.tif", "wb") as f:
            f.write(response.read())  # Using .read() instead of .content

    # Process the response as you originally intended
    with MemoryFile(response.read()) as memfile:
        datasets.append(memfile.open())

# Merge the datasets
merged_dataset, merged_transform = rasterio.merge.merge(datasets)

# Save the merged dataset to a GeoTIFF file
original_geotiff_path = os.path.join(args.output_location, 'height_4km_download.tif')
with rasterio.open(original_geotiff_path, 'w', driver='GTiff', height=merged_dataset.shape[1],
                   width=merged_dataset.shape[2], count=1, dtype=str(merged_dataset.dtype),
                   crs=epsg25833, transform=merged_transform) as original_dst:
    original_dst.write(merged_dataset)

print("Height GeoTIFF Information:")
print(f"  CRS: {epsg25833}")
print(f"  Transform: {merged_transform}")
print(f"  Width: {merged_dataset.shape[2]}, Height: {merged_dataset.shape[1]}")
print(f"  Pixel Size: 1 meter, 1 meter")
print(f"GeoTIFF saved to {original_geotiff_path}")
