import tkinter as tk
from tkinter import filedialog

from reorientation_gui.state import AppState
from reorientation_gui.widgets.file_dialog import FileDialog

# from image_registration_gui.state import app_state
# from image_registration_gui.widgets.file_dialog import FileDialog

class MenuFile(tk.Menu):
    """
    The File menu containing options to open images and to
    save the current state.
    """

    def __init__(self, menu_bar, root, app_state):
        super().__init__(menu_bar)
        self.app_state = app_state

        menu_bar.add_cascade(menu=self, label="File")
        root.bind("<Control-s>", lambda event: self.save())

        # add commands
        self.add_command(label="Open", command=self.open)
        self.add_command(label="Save", command=self.save)
        self.add_command(label="Save as", command=self.save_as)

        # create a variable for the filename to save as
        self.save_filename = tk.StringVar(value="")
        # disable the save command
        self.entryconfig(1, state=tk.DISABLED)
        # only enable the `save` command once a filename has been
        # specified by using `save as`
        self.save_filename.trace_add(
            "write",
            lambda *args: self.entryconfig(
                1, state=(tk.DISABLED if self.save_filename.get() == "" else tk.ACTIVE)
            ),
        )

    def open(self):
        print("Open")
        FileDialog(self.app_state)

    def save(self):
        print("Save")
        # if self.save_filename.get() == "":
            # return

        # app_state.save(self.save_filename.get())

    def save_as(self):
        print("Save as")
        # self.save_filename.set(filedialog.asksaveasfilename())
        # self.save()


class MenuBar(tk.Menu):
    """
    Menu bar of the app.
    """

    def __init__(self, parent, app_state: AppState):
        super().__init__(parent)

        parent.option_add("*tearOff", False)
        parent["menu"] = self

        self.app_state = app_state
        self.menu_file = MenuFile(self, parent, app_state)

