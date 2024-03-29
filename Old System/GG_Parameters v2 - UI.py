import tkinter as tk
from tkinter import simpledialog
import json
import csv

# Function to get new coordinates from the user
def get_new_coordinates():
    root = tk.Tk()
    root.withdraw()  # Hide the main window

    # Prompt for new coordinates
    new_coords = simpledialog.askstring("Input", "Enter new coordinates (lat, lon):",
                                        parent=root)
    root.destroy()
    return new_coords

def main():
    # Original parameters
    parameters = {
        "center_lat": 62.471192157088616,
        "center_lon": 6.158009308952611,
        "output_location": r"X:\Dropbox\! Prosjekter\GEOS\01 Assets\GGrabber Output"
    }

    # Get new coordinates from the user
    new_coords = get_new_coordinates()
    if new_coords:
        try:
            lat, lon = map(float, new_coords.split(','))
            parameters["center_lat"] = lat
            parameters["center_lon"] = lon
        except ValueError:
            print("Invalid coordinates format. Using default coordinates.")

    # Write parameters to a JSON file
    with open('parameters.json', 'w') as f:
        json.dump(parameters, f)
    
    # # Write parameters to a CSV file
    # with open('parameters.csv', 'w', newline='') as f:
    #     writer = csv.writer(f)
    #     for key, value in parameters.items():
    #         writer.writerow([key, value])
    #         print ("data written as csv file")

    print("Parameters updated and saved to 'parameters.json' and 'parameters.csv'.")

if __name__ == "__main__":
    main()
