import os

import pandas as pd
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
        root.bind(
            "<Control-s>",
            lambda event: (
                self.save() if self.save_filename.get() != "" else self.save_as()
            ),
        )

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
        FileDialog(self.app_state)

    def save(self):
        if self.save_filename.get() == "":
            return

        _data = self.app_state.reorientation_state.to_dict()
        _data["filename"] = self.app_state.file_image_state_spect.filename.value

        _dataframe = dict([(key, [value]) for key, value in _data.items()])
        _dataframe = pd.DataFrame(_dataframe)

        if os.path.isfile(self.save_filename.get()):
            data = pd.read_csv(self.save_filename.get())

            if len(data[data["filename"] == _data["filename"]]) == 1:
                data.loc[
                    data["filename"] == _data["filename"],
                    [
                        "angle_x",
                        "angle_y",
                        "angle_z",
                        "center_x",
                        "center_y",
                        "center_z",
                    ],
                ] = (
                    _data["angle_x"],
                    _data["angle_y"],
                    _data["angle_z"],
                    _data["center_x"],
                    _data["center_y"],
                    _data["center_z"],
                )
            else:
                _data = dict([(key, [value]) for key, value in _data.items()])
                data = pd.concat([data, _dataframe], ignore_index=True)
        else:
            data = _dataframe

        data.sort_values(by="filename", inplace=True)
        data.to_csv(self.save_filename.get(), index=False)

    def save_as(self):
        self.save_filename.set(filedialog.asksaveasfilename())
        self.save()


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
