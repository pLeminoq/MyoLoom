"""
Components of the menu bar.
"""

import json
import os

import pandas as pd
import tkinter as tk
from tkinter import filedialog

from ..state import AppState
from .file_dialog import FileDialog


class MenuFile(tk.Menu):
    """
    The File menu containing options to
      * open an image
      * save the current state
      * restore the state
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
        self.add_command(label="Load", command=self.load)

        self.add_command(
            label="Export Reorientation", command=self.export_reorientation
        )
        self.add_command(
            label="Import Reorientation", command=self.import_reorientation
        )

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

    def load_reorientation(self):
        """
        Query the user to open a CSV-file to restore the reorientation parameters.
        """
        filename = filedialog.askopenfilename()

        data = pd.read_csv(filename)

        image_filename = os.path.basename(self.app_state.filename.value)
        rows = data[data["filename"] == image_filename]

        if len(rows) == 0:
            print(
                f"Could not find reorientation for image {image_filename} in {filename}"
            )
            return

        row = rows.iloc[0]

        center_phys = tuple(
            map(float, (row["center_x"], row["center_y"], row["center_z"]))
        )
        center = self.app_state.sitk_img_state.value.TransformPhysicalPointToIndex(
            center_phys
        )
        with self.app_state.reorientation_state as state:
            state.angle_state.x.value = float(row["angle_x"])
            state.angle_state.y.value = float(row["angle_y"])
            state.angle_state.z.value = float(row["angle_z"])
            state.center_state.x.value = center[0]
            state.center_state.y.value = center[1]
            state.center_state.z.value = center[2]

    def open(self):
        """
        Open a new image with a user dialog.
        """
        FileDialog(self.app_state)

    def save(self):
        """
        Save the current reorientation to a file.
        """
        if self.save_filename.get() == "":
            return

        with open(self.save_filename.get(), mode="w") as f:
            json.dump(self.app_state.serialize(), f, indent=2)

    def load(self):
        filename = filedialog.askopenfile()

        with open(filename, mode="r") as f:
            self.app_state.deserialize(json.load(f))

    def import_reorientation(self):
        pass

    def export_reorientation(self):
        filename = filedialog.asksaveasfilename()

        sitk_img = self.app_state.sitk_img.value
        reorientation = self.app_state.reorientation

        center = tuple(reorientation.center.values())
        center_phys = sitk_img.TransformContinuousIndexToPhysicalPoint(center)

        _data = {}
        _data.update(
            [
                (f"angle_{key}", state.value)
                for key, state in reorientation.angle.dict().items()
            ]
        )
        _data.update(
            [
                ("center_x", center_phys[0]),
                ("center_y", center_phys[1]),
                ("center_z", center_phys[2]),
            ]
        )
        _data["filename"] = os.path.basename(self.app_state.filename.value)

        _dataframe = dict([(key, [value]) for key, value in _data.items()])
        _dataframe = pd.DataFrame(_dataframe)

        # data.sort_values(by="filename", inplace=True)
        data.to_csv(filename, index=False)

    def save_as(self):
        """
        Query the user to select a file for saving and then trigger `save()`.
        """
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
