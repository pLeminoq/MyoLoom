import tkinter as tk
from tkinter import ttk
from typing import List, Optional, Tuple

from reacTk.state import PointState
from reacTk.widget.label import Label, LabelState
from reacTk.widget.canvas.line import Line, LineData, LineState, LineStyle
from reacTk.widget.canvas.text import Text, TextData, TextState, TextStyle
from widget_state import HigherOrderState, DictState, ListState, IntState, StringState
from widget_state.util import compute

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
        line_style: Optional[LineStyle] = None,
        text_color: Optional[StringState] = None,
        text_offset: Optional[IntState] = None,
    ):
        super().__init__()

        self.title = title
        self.axis_labels = axis_labels
        self.slice_view_state = slice_view_state

        self.line_style = (
            line_style
            if line_style is not None
            else LineStyle(color="green", dash=ListState([IntState(8), IntState(5)]))
        )
        self.text_color = text_color if text_color is not None else StringState("white")
        self.text_offset = text_offset if text_offset is not None else IntState(12)


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
        image = self.slice_view.image

        left = compute(
            [canvas._state, state.slice_view_state.sitk_img],
            lambda: PointState(
                *self.slice_view.image.to_canvas(
                    0, state.slice_view_state.sitk_img.value.GetSize()[1] // 2
                )
            ),
        )
        right = compute(
            [canvas._state, state.slice_view_state.sitk_img],
            lambda: PointState(
                *self.slice_view.image.to_canvas(
                    state.slice_view_state.sitk_img.value.GetSize()[0],
                    state.slice_view_state.sitk_img.value.GetSize()[1] // 2,
                )
            ),
        )
        top = compute(
            [canvas._state, state.slice_view_state.sitk_img],
            lambda: PointState(
                *self.slice_view.image.to_canvas(
                    state.slice_view_state.sitk_img.value.GetSize()[0] // 2, 0
                )
            ),
        )
        bottom = compute(
            [canvas._state, state.slice_view_state.sitk_img],
            lambda: PointState(
                *self.slice_view.image.to_canvas(
                    state.slice_view_state.sitk_img.value.GetSize()[0] // 2,
                    state.slice_view_state.sitk_img.value.GetSize()[1],
                )
            ),
        )

        self.line_h = Line(canvas, LineState(LineData(left, right), state.line_style))
        self.line_v = Line(canvas, LineState(LineData(top, bottom), state.line_style))

        self.text_left = Text(
            canvas,
            TextState(
                data=TextData(
                    text=state.axis_labels.left,
                    position=compute(
                        [left, state.text_offset],
                        lambda: PointState(
                            left.x.value + state.text_offset.value, left.y.value
                        ),
                    ),
                ),
                style=TextStyle(color=state.text_color, anchor="center", angle=90),
            ),
        )
        self.text_right = Text(
            canvas,
            TextState(
                data=TextData(
                    text=state.axis_labels.right,
                    position=compute(
                        [right, state.text_offset],
                        lambda: PointState(
                            right.x.value - state.text_offset.value, right.y.value
                        ),
                    ),
                ),
                style=TextStyle(color=state.text_color, anchor="center", angle=90),
            ),
        )
        self.text_top = Text(
            canvas,
            TextState(
                data=TextData(
                    text=state.axis_labels.top,
                    position=compute(
                        [top, state.text_offset],
                        lambda: PointState(
                            top.x.value, top.y.value + state.text_offset.value
                        ),
                    ),
                ),
                style=TextStyle(color=state.text_color, anchor="center"),
            ),
        )
        self.text_bottom = Text(
            canvas,
            TextState(
                data=TextData(
                    text=state.axis_labels.bottom,
                    position=compute(
                        [bottom, state.text_offset],
                        lambda: PointState(
                            bottom.x.value, bottom.y.value - state.text_offset.value
                        ),
                    ),
                ),
                style=TextStyle(color=state.text_color, anchor="center"),
            ),
        )
