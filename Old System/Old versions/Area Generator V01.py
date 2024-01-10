from geopy import Point
from geopy.distance import geodesic
from pyproj import Transformer
import tkinter as tk

# Set up transformer
transformer = Transformer.from_crs("EPSG:4326", "EPSG:25833")

def calculate_bounding_box():
    # clear previous results
    results_text.delete("1.0", tk.END)

    # get center coordinates and square size from user inputs
    coords_str = coords_entry.get()
    square_size_km = float(size_entry.get())
    coords_list = [float(coord) for coord in coords_str.split(",")]
    center = Point(coords_list[0], coords_list[1])

    # calculate half size for offset
    half_size = square_size_km / 2

    # calculate bounding box in geographic coordinates
    north_geog = geodesic(kilometers=half_size).destination(point=center, bearing=0).latitude
    south_geog = geodesic(kilometers=half_size).destination(point=center, bearing=180).latitude

    # calculate west and east geog using north_geog and south_geog
    west_geog = geodesic(kilometers=half_size).destination(point=Point(north_geog, center.longitude), bearing=270).longitude
    east_geog = geodesic(kilometers=half_size).destination(point=Point(south_geog, center.longitude), bearing=90).longitude

    # convert geographic coordinates to UTM 33N coordinates
    west, south = transformer.transform(south_geog, west_geog)
    east, north = transformer.transform(north_geog, east_geog)

    # update text widget to display bounding box coordinates
    results_text.insert(tk.END, f"West: {west}\n")
    results_text.insert(tk.END, f"South: {south}\n")
    results_text.insert(tk.END, f"East: {east}\n")
    results_text.insert(tk.END, f"North: {north}\n")

# create main window
window = tk.Tk()
window.title("Bounding Box Calculator")

# create entry fields for center coordinates and square size
coords_entry = tk.Entry(window)
coords_entry.insert(0, "Enter center coordinates (lat,lon)")
size_entry = tk.Entry(window)
size_entry.insert(0, "Enter area size in km")

# create text widget to display bounding box coordinates
results_text = tk.Text(window, height=4, width=50)

# create button to calculate bounding box
calculate_button = tk.Button(window, text="Calculate", command=calculate_bounding_box)

# add widgets to window
coords_entry.pack()
size_entry.pack()
calculate_button.pack()
results_text.pack()

# start main event loop
window.mainloop()
