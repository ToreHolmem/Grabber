import requests
import json
import argparse
import os
import numpy as np
from PIL import Image

parser = argparse.ArgumentParser(description="Export a map image for a specific bounding box.")
parser.add_argument("min_x", type=float, help="Minimum X coordinate of the bounding box.")
parser.add_argument("min_y", type=float, help="Minimum Y coordinate of the bounding box.")
parser.add_argument("max_x", type=float, help="Maximum X coordinate of the bounding box.")
parser.add_argument("max_y", type=float, help="Maximum Y coordinate of the bounding box.")
parser.add_argument("temp_dir", type=str, help="Temporary directory path for storing intermediate files, not used in this script.")
parser.add_argument("final_output_path", type=str, help="Path to save the final map image.")
args = parser.parse_args()

import os
from PIL import Image
import numpy as np

def process_image(png_path):
    with Image.open(png_path) as img:
        # Ensure the image is in RGBA mode for processing
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
        data = np.array(img)
        
        # Create a binary mask where pixels are white if they had non-zero alpha, and black otherwise
        binary_mask = np.zeros(data.shape[:2], dtype=np.uint8)
        binary_mask[data[:, :, 3] != 0] = 255  # Set to white where alpha is not 0
        
        # Convert the binary mask back to an image in grayscale
        img = Image.fromarray(binary_mask, mode='L')
        
        # Rotate the image 90 degrees clockwise
        img = img.rotate(-90, expand=True)
        
        # Save the processed and rotated image back as PNG, overwriting the original file
        img.save(png_path)
        print(f"Processed, rotated, and saved the image as binary mask in PNG format: {png_path}")


with open('token.json', 'r') as file:
    token_data = json.load(file)
token = token_data['token']

with open('AR5_Layers.json', 'r') as file:
    layer_info = json.load(file)["layers"]

bbox_tuple = (args.min_x, args.min_y, args.max_x, args.max_y)
bbox = ','.join(map(str, bbox_tuple))

export_url = 'https://services.geodataonline.no/arcgis/rest/services/Geomap_UTM33_EUREF89/GeomapArealressurs/MapServer/export'

for layer in layer_info:
    params = {
        'f': 'image',
        'format': 'png32',  # Specify PNG format that includes an alpha channel
        'bbox': bbox,
        'size': '4033,4033',
        'bboxSR': '25833',
        'imageSR': '25833',
        'layers': f'show:{layer["id"]}',
        'token': token,
        'transparent': 'true',  # Ensure transparency is enabled
    }

    response = requests.get(export_url, params=params)

    output_path = os.path.join(os.path.dirname(args.final_output_path), f'AR5_{layer["name"]}.png')

    if response.status_code == 200:
        with open(output_path, 'wb') as file:
            file.write(response.content)
        
        # Process the image to fill alpha with black and others with white
        process_image(output_path)

        print(f"Map exported and processed. Saved to: {output_path}")
    else:
        print(f"Failed to retrieve data for layer {layer['name']}. Status code:", response.status_code)
        print("Response content:", response.text)

print("Export Map operation completed.")

# Define the paths to your images
image_paths = [
    os.path.join(os.path.dirname(args.final_output_path), 'AR5_Barskog.png'),
    os.path.join(os.path.dirname(args.final_output_path), 'AR5_Blandingsskog.png'),
    os.path.join(os.path.dirname(args.final_output_path), 'AR5_Lauvskog.png')
]

# Initialize an array to hold the combined binary mask
combined_mask = None

# Process each image
for path in image_paths:
    with Image.open(path) as img:
        # Convert image to binary format (True for white, False for black)
        binary_mask = np.array(img) > 128  # Assuming the image is grayscale, threshold at the middle
        
        # If the combined mask is not initialized, copy the current mask
        if combined_mask is None:
            combined_mask = binary_mask
        else:
            # Combine the current mask with the combined mask using logical OR
            combined_mask |= binary_mask

# Convert the combined mask back to an image (255 for True/white, 0 for False/black)
combined_image = Image.fromarray(np.uint8(combined_mask) * 255, 'L')

# Define the path for the new image
new_image_path = os.path.join(os.path.dirname(args.final_output_path), 'AR5_All_Skog.png')

# Save the new image
combined_image.save(new_image_path)

print(f"All white areas merged and saved to: {new_image_path}")

def merge_images_to_color_channels(paths, output_path):
    # Initialize an empty array for the RGB channels
    channels = []

    # Load each image and extract the white areas as a channel
    for path in paths:
        with Image.open(path) as img:
            # Ensure the image is in grayscale mode for processing
            if img.mode != 'L':
                img = img.convert('L')
            data = np.array(img)
            
            # Use the white areas for the channel (white is 255 in grayscale)
            channel = data
            channels.append(channel)

    # Combine the individual channels into a single RGB image
    combined_image = np.stack(channels, axis=-1)

    # Convert the numpy array back to a PIL image
    combined_image = Image.fromarray(np.uint8(combined_image), 'RGB')

    # Save the new image
    combined_image.save(output_path)
    print(f"Combined image saved to: {output_path}")

# Use the new function to combine images into color channels
color_channels_image_path = os.path.join(os.path.dirname(args.final_output_path), 'AR5_Combined_Color_Channels.png')
merge_images_to_color_channels(image_paths, color_channels_image_path)

