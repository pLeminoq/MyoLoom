import argparse
import tkinter as tk
from tkinter import ttk

from .app import App
from .polar_map.main import App as PolarMapApp
from .polar_map.state import AppState as PolarMapState
from .state import AppState
from .widget.file_dialog import FileDialog
from .widget.menu import MenuBar

parser = argparse.ArgumentParser(
    description="GUI for the reorientation of myocardial perfusion SPECT images.",
    formatter_class=argparse.ArgumentDefaultsHelpFormatter,
)
parser.add_argument(
    "--file", type=str, help="provide a SPECT image file for reorientation"
)
parser.add_argument(
    "--state", type=str, help="provide a SPECT image file for reorientation"
)
args = parser.parse_args()

import json

# create the app state
app_state = AppState()

# set initial file from args
if args.file is not None:
    app_state.filename.value = args.file

if args.state is not None:
    with open(args.state, mode="r") as f:
        app_state.deserialize(json.load(f))

root = tk.Tk()
root.title("MyoLoom")
root.rowconfigure(0, weight=1)
root.columnconfigure(0, weight=1)

# open file dialog after startup if no file is specified
if app_state.filename.value == "":
    root.after(50, lambda *args: FileDialog(app_state).grab_set())

style = ttk.Style()
style.theme_use("clam")

menu_bar = MenuBar(root, app_state)
notebook = ttk.Notebook(root)
notebook.grid(sticky="nswe")
notebook.rowconfigure(0, weight=1)
notebook.columnconfigure(0, weight=1)

# start the app
app = App(notebook, app_state)
app.grid(sticky="nswe")

polar_map_state = PolarMapState()
polar_map_app = PolarMapApp(notebook, polar_map_state)
polar_map_app.grid(sticky="nswe")

notebook.add(app, text="Reorientation")
notebook.add(polar_map_app, text="Polar Map")
notebook.select(1)

def test(event):
    if event.widget.index(notebook.select()) == 1:
        polar_map_state.input_image.set(app_state.img_reoriented.value)

notebook.bind("<<NotebookTabChanged>>", test)

root.bind("<Key-q>", lambda event: exit(0))
root.mainloop()
