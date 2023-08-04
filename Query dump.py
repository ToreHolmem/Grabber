import requests
from PIL import Image
from io import BytesIO

# Replace with a specific bounding box for testing
bbox = (min_x, min_y, max_x, max_y)
width = 256
height = 256

image_url = 'https://services.geodataonline.no/arcgis/rest/services/Geocache_UTM33_EUREF89/GeocacheBilder/MapServer/export?bbox={},{},{},{}&bboxSR=32633&imageSR=32633&size={},{}&format=png&transparent=false&f=image'.format(*bbox, width, height)
response = requests.get(image_url)
image = Image.open(BytesIO(response.content))
image.show()
