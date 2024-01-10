import requests

def test_api_connection():
    url = "https://services.geodataonline.no/arcgis/rest/services/Geomap_UTM33_EUREF89/GeomapBasis2/MapServer/82/query"
    params = {
        "where": "1=1",
        "outFields": "*",
        "f": "geojson",
        "token": "SM9vAJIp4ApegEaDONqbTuedGa_D69wuiJMPFvayMBu6u6x3FMRNcau4PjVgvO_B"  # your token here
    }

    response = requests.get(url, params=params)

    print(f"HTTP Status Code: {response.status_code}")
    
    if response.status_code == 200:
        print("Successfully connected to the API.")
        print("Response Data:", response.json())
    else:
        print(f"Failed to connect to the API. HTTP Status Code: {response.status_code}")

if __name__ == "__main__":
    test_api_connection()
