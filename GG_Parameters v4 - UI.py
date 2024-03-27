import tkinter as tk
from tkinter import Checkbutton, IntVar, Listbox, END
import json

# Assuming PARAMETERS_PATH is defined (for loading/saving script configs)
PARAMETERS_PATH = 'parameters.json'
HISTORY_PATH = 'history.json'

def load_parameters():
    try:
        with open(PARAMETERS_PATH, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_parameters(parameters):
    with open(PARAMETERS_PATH, 'w') as f:
        json.dump(parameters, f, indent=4)

def load_history():
    try:
        with open(HISTORY_PATH, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def save_history(history):
    with open(HISTORY_PATH, 'w') as f:
        json.dump(history, f)

def update_history_listbox(history, listbox):
    listbox.delete(0, END)  # Clear current entries
    for entry in history:
        listbox.insert(END, f"{entry['name']}: {entry['coords']}")

def on_history_select(event, history_listbox, history, coords_entry, name_entry):
    index = history_listbox.curselection()
    if index:
        index = index[0]
        selected_item = history[index]
        coords_entry.delete(0, tk.END)
        coords_entry.insert(0, selected_item['coords'])
        name_entry.delete(0, tk.END)
        name_entry.insert(0, selected_item['name'])



def main():
    parameters = load_parameters()
    history = load_history()
    script_configs = parameters.get('scripts', {})

    root = tk.Tk()
    root.title("Geospatial Processing Configuration")

    # Coordinate Entry Section
    tk.Label(root, text="Coordinates (lat, lon):").pack(padx=10, pady=5)
    coords_entry = tk.Entry(root)
    coords_entry.pack(padx=10, pady=5)

    tk.Label(root, text="Location Name:").pack(padx=10, pady=5)
    name_entry = tk.Entry(root)
    name_entry.pack(padx=10, pady=5)

    def on_submit():
        coords = coords_entry.get()
        name = name_entry.get()
        if coords and name:
            try:
                lat, lon = map(float, coords.split(','))
                parameters["center_lat"] = lat
                parameters["center_lon"] = lon
                if not any(entry['coords'] == coords and entry['name'] == name for entry in history):
                    history.append({"name": name, "coords": coords})
                    save_history(history)
                    update_history_listbox(history, history_listbox)
                save_parameters(parameters)
                print("Parameters updated and saved.")
                root.destroy()  # Close the tkinter window
            except ValueError:
                print("Invalid coordinates format.")
        else:
            print("Please enter both coordinates and a location name.")




    submit_btn = tk.Button(root, text="Submit", command=on_submit)
    submit_btn.pack(padx=10, pady=5)

    history_listbox = Listbox(root)
    history_listbox.pack(padx=10, pady=5, fill=tk.X, expand=True)
    # Bind the event to the listbox with a lambda to pass the widgets
    history_listbox.bind('<<ListboxSelect>>', lambda event: on_history_select(event, history_listbox, history, coords_entry, name_entry))

    update_history_listbox(history, history_listbox)

    # Script Execution & Cropping Settings
    checkboxes_frame = tk.LabelFrame(root, text="Script Settings")
    checkboxes_frame.pack(fill=tk.X, padx=10, pady=10)

    checkboxes = {}
    for script_name, config in script_configs.items():
        frame = tk.Frame(checkboxes_frame)
        frame.pack(fill=tk.X)
        
        execute_var = IntVar(value=config.get('execute', 0))
        crop_var = IntVar(value=config.get('crop', 0))

        execute_cb = Checkbutton(frame, text=f"Execute {script_name}", variable=execute_var)
        execute_cb.pack(side=tk.LEFT)

        crop_cb = Checkbutton(frame, text="Crop", variable=crop_var)
        crop_cb.pack(side=tk.LEFT)

        checkboxes[script_name] = (execute_var, crop_var)

    def on_save_settings():
        # Update parameters based on checkboxes
        for script_name, (execute_var, crop_var) in checkboxes.items():
            script_configs[script_name]['execute'] = bool(execute_var.get())
            script_configs[script_name]['crop'] = bool(crop_var.get())
        
        save_parameters(parameters)
        print("Script settings saved.")

    save_settings_btn = tk.Button(root, text="Save Script Settings", command=on_save_settings)
    save_settings_btn.pack(pady=10)

    root.mainloop()

if __name__ == "__main__":
    main()
