import requests
from xml.etree import ElementTree

url = 'https://wcs.geonorge.no/skwms1/wcs.hoyde-dtm-nhm-25833?service=wcs&request=getcapabilities'

# Send the GetCapabilities request
response = requests.get(url)

# Parse the response
tree = ElementTree.fromstring(response.content)

# Define the namespace
namespace = {'wcs': 'http://www.opengis.net/wcs/1.0.0'}

# Find the Constraint elements
constraints = tree.findall('.//wcs:Constraint', namespace)

# Iterate over the constraints and print the name and value of each one
for constraint in constraints:
    name = constraint.find('wcs:Name', namespace)
    value = constraint.find('wcs:Value', namespace)
    if name is not None and value is not None:
        print(f"{name.text}: {value.text}")
