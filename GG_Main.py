import GG_Script_Runner as script_runner
import json
import subprocess

# Run GG_Parameters.py to update the JSON file
subprocess.run(["python", "GG_Parameters.py"])

# Load parameters from a JSON file
with open('parameters.json', 'r') as f:
    parameters = json.load(f)

scripts_to_run = [
    # 'Download_Aerial_1km.py',
    # 'Download_Aerial_4km.py',
    # 'Download_Aerial_60km.py',
    # 'Download_Height_4km.py',
    # 'Download_Height_60km.py',
    'Download_SR16_4km_Local.py',
    'GG_Treatment.py',
]

script_runner.run_scripts(scripts_to_run, parameters["center_lat"], parameters["center_lon"], parameters["output_location"])

