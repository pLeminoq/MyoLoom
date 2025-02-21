import tkinter as tk
from tkinter import ttk
from typing import Optional

from reacTk.decorator import stateful
from reacTk.widget.label import Label, LabelState
from reacTk.state import to_tk_var
from widget_state import NumberState, DictState, StringState


class ScaleState(DictState):
    def __init__(
        self,
        value: NumberState,
        min_value: NumberState,
        max_value: NumberState,
        length: NumberState,
        orientation: Optional[StringState] = None,
        formatter: Optional[StringState] = None,
    ):
        super().__init__()

        self.value = value
        self.min = min_value
        self.max = max_value
        self.length = length if length is not None else IntState(None)
        self.orientation = (
            orientation if orientation is not None else StringState(tk.VERTICAL)
        )
        self.formatter = formatter if formatter is not None else StringState("{:.0f}")


@stateful
class Scale(ttk.Frame):
    def __init__(self, parent: tk.Widget, state: ScaleState):
        super().__init__(parent)

        self.scale = ttk.Scale(
            self,
            orient=state.orientation.value,
            length=state.length.value,
            from_=state.min.value,
            to=state.max.value,
            variable=to_tk_var(state.value),
        )

        state.value.on_change(lambda _: self.scale.focus())

        self.label_min = Label(self, LabelState(""))
        self.label_max = Label(self, LabelState(""))
        self.label_current = Label(self, LabelState(""))

        if state.orientation.value == tk.HORIZONTAL:
            self.scale.grid(column=1, row=0, padx=5)
            self.label_min.grid(column=0, row=0, sticky=tk.N)
            self.label_max.grid(column=2, row=0)
            self.label_current.grid(column=1, row=1)
        else:
            self.scale.grid(column=0, row=1, pady=5)
            self.label_min.grid(column=0, row=0)
            self.label_max.grid(column=0, row=2)
            self.label_current.grid(column=1, row=1, padx=(0, 10))

    def draw(self, state: ScaleState):
        self.scale.configure(
            orient=state.orientation.value,
            length=state.length.value,
            from_=state.min.value,
            to=state.max.value,
        )

        self.label_current._state.set(state.formatter.value.format(state.value.value))
        self.label_min._state.set(state.formatter.value.format(state.min.value))
        self.label_max._state.set(state.formatter.value.format(state.max.value))
