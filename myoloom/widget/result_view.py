import tkinter as tk
from tkinter import ttk
from typing import List, Tuple

from reacTk.state import PointState
from reacTk.widget.label import Label, LabelState
from reacTk.widget.canvas.line import Line, LineData, LineState, LineStyle
from widget_state import HigherOrderState, DictState

from .slice_view import SliceView, SliceViewState


class AxisLabelState(DictState):

    def __init__(self, top: str, left: str, right: str, bottom: str):
        """
        Define labels for the top, left, right, and bottom positions of the displayed image.
        """
        super().__init__()

        self.top = top
        self.left = left
        self.bottom = bottom
        self.right = right


class ResultViewState(HigherOrderState):

    def __init__(
        self,
        title: str,
        axis_labels: AxisLabelState,
        slice_view_state: SliceViewState,
    ):
        super().__init__()

        self.title = title
        self.axis_labels = axis_labels
        self.slice_view_state = slice_view_state


class ResultView(ttk.Frame):

    def __init__(self, parent: tk.Widget, state: ResultViewState):
        super().__init__(parent)

        self._state = state

        self.title = Label(self, state.title)
        self.title.grid(column=0, row=0)

        self.slice_view = SliceView(self, state.slice_view_state)
        self.slice_view.grid(column=0, row=1, sticky="nswe")

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=9)

        canvas = self.slice_view.canvas
        canvas.bind("<Button-1>", lambda _: canvas.focus_force())

        left = PointState(0, 0)
        left.depends_on(
            [canvas._state, state.slice_view_state.sitk_img],
            lambda: PointState(
                *self.slice_view.image.to_canvas(
                    0, state.slice_view_state.sitk_img.value.GetSize()[1] // 2
                )
            ),
        )

        right = PointState(0, 0)
        right.depends_on(
            [canvas._state, state.slice_view_state.sitk_img],
            lambda: PointState(
                *self.slice_view.image.to_canvas(
                    state.slice_view_state.sitk_img.value.GetSize()[0],
                    state.slice_view_state.sitk_img.value.GetSize()[1] // 2,
                )
            ),
        )

        top = PointState(0, 0)
        top.depends_on(
            [canvas._state, state.slice_view_state.sitk_img],
            lambda: PointState(
                *self.slice_view.image.to_canvas(
                    state.slice_view_state.sitk_img.value.GetSize()[0] // 2, 0
                )
            ),
        )

        bottom = PointState(0, 0)
        bottom.depends_on(
            [canvas._state, state.slice_view_state.sitk_img],
            lambda: PointState(
                *self.slice_view.image.to_canvas(
                    state.slice_view_state.sitk_img.value.GetSize()[0] // 2,
                    state.slice_view_state.sitk_img.value.GetSize()[1],
                )
            ),
        )

        self.line_h = Line(
            canvas, LineState(LineData(left, right), LineStyle(color="green"))
        )
        self.line_v = Line(
            canvas, LineState(LineData(top, bottom), LineStyle(color="green"))
        )

        # w, h = state.slice_view_state.resolution_state.values()
        # canvas.create_line((0, h // 2), (w, h // 2), fill="green", dash=(8, 5))
        # canvas.create_line((w // 2, 0), (w // 2, h), fill="green", dash=(8, 5))
        #
        # canvas.create_text(w // 2, 10, fill="green", text=state.axis_labels.top.value)
        # canvas.create_text(25, h // 2, fill="green", text=state.axis_labels.left.value)
        # canvas.create_text(
        #     w - 25, h // 2, fill="green", text=state.axis_labels.right.value
        # )
        # canvas.create_text(
        #     w // 2, h - 10, fill="green", text=state.axis_labels.bottom.value
        # )
