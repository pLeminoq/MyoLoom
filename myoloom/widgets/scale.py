from typing import Callable, Tuple, Union

import tkinter as tk
from tkinter import ttk

from ..state import IntState, FloatState, HigherState

Number = Union[int, float]
NumberState = Union[IntState, FloatState]


class ScaleState(HigherState):

    def __init__(
        self,
        number_state: NumberState,
        value_range: Tuple[Number, Number],
        length: int,
        orientation: str = tk.HORIZONTAL,
        formatter: Callable[[Number], str] = lambda x: f"{x}",
    ):
        """
        State of a scale.

        Parameters
        ----------
        number_state: NumberState
            state representing the value of the acle
        value_range: tuple of number,
            minimal and maximal value of the scale
        length: int
            length of the scale in pixels
        orientation: str
            orientation of the scale: horizontal or vertical
        formatter: callable
            convert the value of the scale to str for visualization
        """
        super().__init__()

        self.number_state = number_state
        self._value_range = value_range
        self._length = length
        self._orientation = orientation
        self._formatter = formatter


class Scale(tk.Frame):

    def __init__(self, parent: tk.Frame, state: ScaleState):
        """
        Scale widget with which user can select numerical values inside a value range.
        """
        super().__init__(parent)

        self.state = state

        self.tk_var = (
            tk.IntVar(value=self.state.number_state.value)
            if type(self.state.number_state) == IntState
            else tk.DoubleVar(value=self.state.number_state.value)
        )

        self.scale = ttk.Scale(
            self,
            orient=self.state._orientation,
            length=self.state._length,
            from_=self.state._value_range[0],
            to=self.state._value_range[1],
            variable=self.tk_var,
        )
        self.label_min = tk.Label(
            self, text=self.state._formatter(self.state._value_range[0])
        )
        self.label_max = tk.Label(
            self, text=self.state._formatter(self.state._value_range[1])
        )
        self.label_current = tk.Label(
            self, text=self.state._formatter(self.state.number_state.value)
        )

        self.tk_var.trace_add("write", lambda *args: self.scale.focus())
        self.tk_var.trace_add(
            "write", lambda *args: self.state.number_state.set(self.tk_var.get())
        )

        self.state.number_state.on_change(lambda state: self.tk_var.set(state.value))
        self.state.number_state.on_change(
            lambda state: self.label_current.config(
                text=self.state._formatter(state.value)
            )
        )

        if self.state._orientation == tk.HORIZONTAL:
            self.label_min.grid(column=0, row=0, sticky=tk.N)
            self.scale.grid(column=1, row=0, padx=5)
            self.label_max.grid(column=2, row=0)
            self.label_current.grid(column=1, row=1)
        else:
            self.label_min.grid(column=0, row=0)
            self.scale.grid(column=0, row=1, pady=5)
            self.label_max.grid(column=0, row=2)
            self.label_current.grid(column=1, row=1, padx=(0, 10))
