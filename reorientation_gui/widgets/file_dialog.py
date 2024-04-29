import os

import tkinter as tk
from tkinter import filedialog, ttk

from reorientation_gui.state import AppState


class FileSelection(tk.Frame):
    """
    Widget used to select a file.

    It displays as: <label> <text> <button>
    The user can either type the filename in the text field or
    open a dialog by clicking on the button.
    """

    def __init__(self, parent: tk.Widget, label: str, init_filename: str = ""):
        """
        Create a new file selection widget.

        Parameters
        ----------
        parent: tk.Widget
            the parent widget
        label: str
            text displayed to the user to identify the kind of file to be opened
        """
        super().__init__(parent)

        self.filename = tk.StringVar(value=init_filename)

        self.label = tk.Label(self, text=f"{label}", anchor=tk.E, width=20)
        self.textfield = ttk.Entry(self, textvariable=self.filename, width=80)
        self.button = ttk.Button(
            self,
            text="Open",
            width=15,
            command=lambda *args: self.filename.set(filedialog.askopenfilename()),
        )

        self.label.grid(column=0, row=0, padx=5)
        self.textfield.grid(column=1, row=0, padx=5)
        self.button.grid(column=2, row=0, padx=(5, 10))


class FileDialog(tk.Toplevel):
    """
    Dialog to select the image to be reoriented.

    The user has to select the image to be reoriented and can optionally specify
    a mu-map/ct.
    """

    def __init__(self, app_state: AppState):
        super().__init__()

        self.frame = tk.Frame(self)
        self.frame.grid()

        self.app_state = app_state

        self.selection_spect = FileSelection(
            self.frame,
            label="Image",
            init_filename=app_state.file_image_state_spect.filename.value,
        )
        self.selection_mu_map = FileSelection(
            self.frame,
            label="MuMap",
            init_filename=app_state.file_image_state_mu_map.filename.value,
        )
        self.button = ttk.Button(self.frame, text="Confirm", command=self.on_confirm)

        self.selection_spect.filename.trace_add("write", self.enable_button)
        self.selection_mu_map.filename.trace_add("write", self.enable_button)

        self.selection_spect.grid(column=0, row=0, pady=5)
        self.selection_mu_map.grid(column=0, row=1, pady=5)
        self.button.grid(column=0, row=2, pady=5)

        self.enable_button()
        self.bind("<Return>", self.on_confirm)

    def selection_is_valid(self):
        """
        Validate if the selection is valid (files exist).
        """
        str_spect = self.selection_spect.filename.get()
        str_mumap = self.selection_mu_map.filename.get()

        valid_spect = os.path.isfile(str_spect)
        valid_mumap = str_mumap == "" or os.path.isfile(str_mumap)
        return valid_spect and valid_mumap

    def enable_button(self, *args):
        """
        Enable/Disable the confirmation button.
        """
        self.button["state"] = tk.ACTIVE if self.selection_is_valid() else tk.DISABLED

    def on_confirm(self, *args):
        """
        Update the app state on confirmation.
        """
        if not self.selection_is_valid():
            return

        self.app_state.file_image_state_spect.filename.value = (
            self.selection_spect.filename.get()
        )
        self.app_state.file_image_state_mu_map.filename.value = (
            self.selection_mu_map.filename.get()
        )

        # remove the dialog after confirmation
        self.destroy()
        self.update()