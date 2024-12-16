import argparse

from .app import App
from .state import AppState
from .widget.file_dialog import FileDialog

parser = argparse.ArgumentParser(
    description="GUI for the reorientation of myocardial perfusion SPECT images.",
    formatter_class=argparse.ArgumentDefaultsHelpFormatter,
)
parser.add_argument(
    "--file", type=str, help="provide a SPECT image file for reorientation"
)
args = parser.parse_args()

# create the app state
app_state = AppState()
# set initial file from args
if args.file is not None:
    app_state.filename.value = args.file

# start the app
app = App(app_state)
# open file dialog after startup if no file is specified
if args.file is None:
    app.after(50, lambda *args: FileDialog(app_state).grab_set())

app.mainloop()
