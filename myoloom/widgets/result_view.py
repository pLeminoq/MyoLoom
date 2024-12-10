from typing import List, Tuple

import SimpleITK as sitk
import tkinter as tk

from reorientation_gui.state import HigherState, SequenceState
from reorientation_gui.widgets.slice_view import SliceView, SliceViewState


class AxisLabelState(SequenceState):

    def __init__(self, top: str, left: str, right: str, bottom: str):
        """
        Define labels for the top, left, right, and bottom positions of the displayed image.
        """
        super().__init__(
            values=[top, left, right, bottom],
            labels=["top", "left", "right", "bottom"],
        )


class ResultViewState(HigherState):

    def __init__(
        self,
        title: str,
        axis_labels: AxisLabelState,
        slice_view_state: SliceViewState,
    ):
        """
        State of the `ResultView` widget.

        Parameters
        ----------
        title: str
            title of the result view, e.g., "Short-Axis View"
        axis_labels: AxisLabelState
            labels of the up, down, left and right directions of the displayed image
        slice_view_state: SliceViewState
            state configuring the image display
        """
        super().__init__()

        self.title = title
        self.axis_labels = axis_labels
        self.slice_view_state = slice_view_state

        self.slice_view_state.slice_state.set(self.slice_view_state.sitk_img_state.value.GetSize()[0] // 2)
        self.slice_view_state.sitk_img_state.on_change(
            lambda sitk_img_state: self.slice_view_state.slice_state.set(
                sitk_img_state.value.GetSize()[0] // 2
            )
        )


class ResultView(tk.Frame):

    def __init__(self, parent: tk.Frame, state: ResultViewState):
        """
        Widget used to display the result of a reorientation.

        It uses a `SliceView` to display an image in one direction.
        In addition, the center of the image is highlighted with a vertical and a horizontal line,
        and labels for axis directions are displayed.
        """
        super().__init__(parent)

        self.state = state

        self.title = tk.Label(self, text=state.title.value)
        self.slice_view = SliceView(self, state.slice_view_state)

        canvas = self.slice_view.canvas
        w, h = state.slice_view_state.resolution_state.values()
        canvas.create_line((0, h // 2), (w, h // 2), fill="green", dash=(8, 5))
        canvas.create_line((w // 2, 0), (w // 2, h), fill="green", dash=(8, 5))

        canvas.create_text(w // 2, 10, fill="green", text=state.axis_labels.top.value)
        canvas.create_text(25, h // 2, fill="green", text=state.axis_labels.left.value)
        canvas.create_text(
            w - 25, h // 2, fill="green", text=state.axis_labels.right.value
        )
        canvas.create_text(
            w // 2, h - 10, fill="green", text=state.axis_labels.bottom.value
        )

        self.title.grid(column=0, row=0)
        self.slice_view.grid(column=0, row=1)
