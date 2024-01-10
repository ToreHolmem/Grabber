import json

# Variables for location and target folder
parameters = {
    "center_lat": 62.471192157088616,
    "center_lon": 6.158009308952611,
    "output_location": r"X:\Dropbox\! Prosjekter\GEOS\01 Assets\Ggrabber Output"
}

# Write parameters to a JSON file
with open('parameters.json', 'w') as f:
    json.dump(parameters, f)

