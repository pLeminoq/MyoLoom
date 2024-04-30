from typing import List, Tuple

import SimpleITK as sitk
import tkinter as tk

from reorientation_gui.state import (
    State,
    ReorientationState,
    IntState,
    SITKImageState,
    TransformedSITKImageState,
)
from reorientation_gui.widgets.slice_view import SliceView, SliceViewState
from reorientation_gui.util import transform_image


class ResultViewState(State):

    def __init__(
        self,
        sitk_img_state: TransformedSITKImageState,
        size,
        title: str,
        axis_labels: List[str],
        mu_map=None,
    ):
        self.mu_map = mu_map
        self.title = title
        self.axis_labels = axis_labels

        _mu_map = None if mu_map is not None else None
        self.slice_view_state = SliceViewState(
            sitk_img_state=sitk_img_state,
            slice=IntState(sitk_img_state.value.GetSize()[0] // 2),
            size=size,
            mu_map=_mu_map,
        )

        # reset slice if a new image is shown
        sitk_img_state._sitk_img_state.on_change(self.reset_slice)

    def reset_slice(self, state):
        print(f"Reset slices...")
        self.slice_view_state.slice.value = state.value.GetSize()[0] // 2


class ResultView(tk.Frame):

    def __init__(self, parent: tk.Frame, state: ResultViewState):
        super().__init__(parent)

        self.state = state

        self.title = tk.Label(self, text=state.title)
        self.slice_view = SliceView(self, state.slice_view_state)

        canvas = self.slice_view.canvas
        size = state.slice_view_state.size
        canvas.create_line(
            (0, size[1] // 2), (size[0], size[1] // 2), fill="green", dash=(8, 5)
        )
        canvas.create_line(
            (size[0] // 2, 0), (size[0] // 2, size[1]), fill="green", dash=(8, 5)
        )

        canvas.create_text(size[0] // 2, 10, fill="green", text=state.axis_labels[0])
        canvas.create_text(25, size[1] // 2, fill="green", text=state.axis_labels[1])
        canvas.create_text(
            size[0] - 25, size[1] // 2, fill="green", text=state.axis_labels[2]
        )
        canvas.create_text(
            size[0] // 2, size[1] - 10, fill="green", text=state.axis_labels[3]
        )

        self.title.grid(column=0, row=0)
        self.slice_view.grid(column=0, row=1)
