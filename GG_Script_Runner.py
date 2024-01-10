# script_runner.py
import subprocess
import time

def run_scripts(scripts, center_lat, center_lon, output_location):
    for script in scripts:
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