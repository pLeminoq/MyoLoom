from reorientation_gui.app import App
from reorientation_gui.state import AppState
from reorientation_gui.widgets.file_dialog import FileDialog

app_state = AppState()
app = App(app_state)
# open file dialog after startup
app.after(50, lambda *args: FileDialog(app_state).grab_set())
app.mainloop()
