import platform
import subprocess
import time

# Define your variables
center_lat = 62.62104190802922
center_lon = 6.854110293340546

# Detect the operating system and use the correct path format
if platform.system() == 'Windows':
    output_location = r"X:\Dropbox\! Prosjekter\Grabber\Output"
else:
    output_location = "/Users/toreholmem/Dropbox/! Prosjekter/Fiksdal/03 Assets/Data/Fra GGrabber"

scripts_to_run = [
     'GG_Aerial_1km.py',
   # 'GG_Aerial_4km.py',
   # 'GG_Aerial_60km.py',
   # 'GG_Height_1km.py',
   # 'GG_Height_4km.py',
   # 'GG_Height_60km.py'
]

for script in scripts_to_run:
    print(f'Starting {script}...')
    start_time = time.time()
    process = subprocess.Popen(['python', script, str(center_lat), str(center_lon), output_location], stdout=subprocess.PIPE)
    while True:
        output = process.stdout.readline()
        if process.poll() is not None:
            break
        if output:
            print(output.strip().decode('utf-8'))
    end_time = time.time()
    print(f'Finished {script} in {end_time - start_time} seconds.\n')

print("All scripts executed.")
