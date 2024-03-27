import requests
import argparse
import rasterio
from rasterio.transform import from_bounds
import json

try:
    print("Opening parameters.json")
    with open('parameters.json') as f:
        parameters = json.load(f)
    print("parameters.json loaded successfully")

    print("Setting up argument parser")
    parser = argparse.ArgumentParser(description='Download height data and process it into a single GeoTIFF.')
    parser.add_argument("min_x", type=float, help="Minimum X coordinate of the bounding box.")
    parser.add_argument("min_y", type=float, help="Minimum Y coordinate of the bounding box.")
    parser.add_argument("max_x", type=float, help="Maximum X coordinate of the bounding box.")
    parser.add_argument("max_y", type=float, help="Maximum Y coordinate of the bounding box.")
    parser.add_argument("temp_dir", type=str, help="Temporary directory path for storing intermediate files.")
    parser.add_argument("final_output_path", type=str, help="Path to save the final merged GeoTIFF.")
    args = parser.parse_args()

    print(f"Arguments parsed: min_x={args.min_x}, min_y={args.min_y}, max_x={args.max_x}, max_y={args.max_y}, temp_dir={args.temp_dir}, final_output_path={args.final_output_path}")

    def download_and_save_tiff(layers, bbox, output_path, service_url):
        print(f"Downloading TIFF with bbox: {bbox} and saving to {output_path}")
        params = {
            'bbox': ','.join(map(str, bbox)),
            'bboxSR': '25833',
            'layers': f'show:{layers}',
            'format': 'png',
            'transparent': 'false',
            'size': '2048,2048',
            'f': 'image'
        }
        response = requests.get(service_url, params=params)
        
        print(f"HTTP response code: {response.status_code}")
        if response.status_code == 200:
            print("Saving downloaded content to GeoTIFF")
            with rasterio.open(output_path, 'w', driver='GTiff',
                               width=2048, height=2048, count=3,
                               dtype='uint8',
                               crs='epsg:25833',
                               transform=from_bounds(*bbox, 2048, 2048)) as dst:
                dst.write(response.content, 1)
            print("GeoTIFF saved successfully")
        else:
            print(f"Failed to download data. Status code: {response.status_code}")

    if __name__ == "__main__":
        print("Executing main block")
        layers = '18'  # Defined in the script for simplicity
        service_url = 'http://services.arcgisonline.com/arcgis/rest/services/Geomap_UTM33_EUREF89/GeomapArealressurs/MapServer/export'
        
        bbox = [args.min_x, args.min_y, args.max_x, args.max_y]
        print(f"Prepared bbox: {bbox}")
        download_and_save_tiff(layers, bbox, args.final_output_path, service_url)
        print("Process completed successfully")

except Exception as e:
    print(f"Error: {e}")
