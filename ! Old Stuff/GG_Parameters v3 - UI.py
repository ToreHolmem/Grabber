import tkinter as tk
from tkinter import Checkbutton, IntVar, Listbox, END
import json

# Path to the history JSON file
HISTORY_PATH = 'history.json'

# Function to load parameters from a JSON file
def load_parameters():
    try:
        with open(PARAMETERS_PATH, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

# Function to save parameters to a JSON file
def save_parameters(parameters):
    with open(PARAMETERS_PATH, 'w') as f:
        json.dump(parameters, f, indent=4)

# Function to load history from a JSON file
def load_history():
    try:
        with open(HISTORY_PATH, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return []

# Function to save history to a JSON file
def save_history(history):
    with open(HISTORY_PATH, 'w') as f:
        json.dump(history, f)

# Function to update the history listbox
def update_history_listbox(history, listbox):
    listbox.delete(0, END)  # Clear current entries
    for entry in history:
        listbox.insert(END, f"{entry['name']}: {entry['coords']}")

def main():
    def on_submit():
        coords = coords_entry.get()
        name = name_entry.get()
        if coords and name:
            try:
                lat, lon = map(float, coords.split(','))
                parameters["center_lat"] = lat
                parameters["center_lon"] = lon
                # Check if entry is already in history
                if not any(entry['coords'] == coords and entry['name'] == name for entry in history):
                    history.append({"name": name, "coords": coords})
                    save_history(history)
                    update_history_listbox(history, history_listbox)
                root.destroy()  # Close the window
                print("Parameters updated and saved.")
            except ValueError:
                print("Invalid coordinates format.")
        else:
            print("Please enter both coordinates and a location name.")

    def on_history_select(event):
        selection = event.widget.curselection()
        if selection:
            index = selection[0]
            entry = history[index]
            coords_entry.delete(0, END)
            coords_entry.insert(0, entry['coords'])
            name_entry.delete(0, END)
            name_entry.insert(0, entry['name'])

    history = load_history()

    # Original parameters
    parameters = {
        "center_lat": 62.471192157088616,
        "center_lon": 6.158009308952611,
        "output_location": r"X:\Dropbox\! Prosjekter\GEOS\01 Assets\GGrabber Output"
    }

    # Setup GUI
    root = tk.Tk()
    root.title("Enter Coordinates and Location Name")

    tk.Label(root, text="Coordinates (lat, lon):").pack(padx=10, pady=5)
    coords_entry = tk.Entry(root)
    coords_entry.pack(padx=10, pady=5)

    tk.Label(root, text="Location Name:").pack(padx=10, pady=5)
    name_entry = tk.Entry(root)
    name_entry.pack(padx=10, pady=5)

    submit_btn = tk.Button(root, text="Submit", command=on_submit)
    submit_btn.pack(padx=10, pady=5)

    history_listbox = Listbox(root)
    history_listbox.pack(padx=10, pady=5, fill=tk.X, expand=True)
    history_listbox.bind('<<ListboxSelect>>', on_history_select)

    update_history_listbox(history, history_listbox)

    root.mainloop()

if __name__ == "__main__":
    main()
