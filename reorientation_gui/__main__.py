import argparse

from reorientation_gui.app import App
from reorientation_gui.state import AppState
from reorientation_gui.widgets.file_dialog import FileDialog

parser = argparse.ArgumentParser()
parser.add_argument("--file", type=str)
args = parser.parse_args()

app_state = AppState()
if args.file is not None:
    app_state.file_image_state_spect.filename.value = args.file

app = App(app_state)
# open file dialog after startup
if args.file is None:
    app.after(50, lambda *args: FileDialog(app_state).grab_set())
app.mainloop()
