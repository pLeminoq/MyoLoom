import tkinter as tk
from tkinter import ttk


class SliceSelector(tk.Frame):
    def __init__(
        self, parent, n_slices: int, current_slice: int = 0, length: int = None
    ):
        super().__init__(parent)

        self.n_slices = n_slices
        self.slice_var = tk.IntVar(value=current_slice)
        self.length = length

        self.scale = ttk.Scale(
            self,
            orient=tk.HORIZONTAL,
            length=self.length,
            from_=0,
            to=self.n_slices,
            variable=self.slice_var,
        )
        self.label_min = tk.Label(self, text=f"{0:{len(str(n_slices))}d}")
        self.label_max = tk.Label(self, text=f"{n_slices}")
        self.label_current = tk.Label(self, text=f"{self.slice_var.get()}")

        self.slice_var.trace_add("write", lambda *args: self.scale.focus())
        self.slice_var.trace_add(
            "write",
            lambda *args: self.label_current.config(text=f"{self.slice_var.get()}"),
        )

        self.label_min.grid(column=0, row=0, sticky=tk.N)
        self.scale.grid(column=1, row=0, padx=5)
        self.label_max.grid(column=2, row=0)
        self.label_current.grid(column=1, row=1)
