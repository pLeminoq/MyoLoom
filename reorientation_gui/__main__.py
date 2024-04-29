from reorientation_gui.state import AppState, StringState
from reorientation_gui.widgets.file_dialog import FileDialog

print("Hallo?")
app_state = AppState(filename_image=StringState(""), filename_mumap=StringState(""))

dialog = FileDialog(app_state)
dialog.grab_set()
dialog.wait_window()
