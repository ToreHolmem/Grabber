import requests
from xml.etree import ElementTree

# Specify the WCS endpoint url for GetCapabilities
url = 'https://wcs.geonorge.no/skwms1/wcs.hoyde-dtm-nhm-25833?service=wcs&request=getcapabilities'

response = requests.get(url)
if response.status_code == 200:
    tree = ElementTree.fromstring(response.content)

    # Pretty print the XML to see its structure
    ElementTree.dump(tree)

    # Additionally, you can search for tags with 'Max' which might indicate constraints
    for elem in tree.findall(".//{http://www.opengis.net/wcs}Max*"):
        print(f"{elem.tag}: {elem.text}")
