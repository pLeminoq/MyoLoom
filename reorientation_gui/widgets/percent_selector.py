import tkinter as tk
from tkinter import ttk


class PercentSelector(tk.Frame):
    def __init__(
            self, parent, current_value: float = 1.0, length: int = None, orientation: str = tk.HORIZONTAL,
    ):
        super().__init__(parent)

        self.slice_var = tk.DoubleVar(value=current_value)
        self.length = length

        self.scale = ttk.Scale(
            self,
            orient=orientation,
            length=length,
            from_=0.001,
            to=1.0,
            variable=self.slice_var,
        )
        self.label_min = tk.Label(self, text=f"  0%")
        self.label_max = tk.Label(self, text=f"100%")
        self.label_current = tk.Label(self, text=f"{100 * self.slice_var.get():.1f}%")

        self.slice_var.trace_add("write", lambda *args: self.scale.focus())
        self.slice_var.trace_add(
            "write",
            lambda *args: self.label_current.config(text=f"{100 * self.slice_var.get():.1f}%"),
        )

        self.label_min.grid(column=0, row=0, sticky=tk.N)
        self.scale.grid(column=1, row=0, padx=5)
        self.label_max.grid(column=2, row=0)
        self.label_current.grid(column=1, row=1)
