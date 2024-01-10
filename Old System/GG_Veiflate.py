import requests

url = "https://services.geodataonline.no/arcgis/rest/services/Geomap_UTM33_EUREF89/GeomapBasis2/MapServer/82/query"
params = {
    'where': '1=1',
    'outFields': 'utvalg_basis',
    'f': 'json',
    'token': 'your_token_here'
}

response = requests.get(url, params=params)
print(response.json())
