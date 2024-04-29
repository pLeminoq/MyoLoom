from typing import List, Tuple

import SimpleITK as sitk
import tkinter as tk

from reorientation_gui.state import State, Reorientation, IntState
from reorientation_gui.widgets.slice_view import SliceView, SliceViewState


class ResultViewState(State):

    def __init__(
        self,
        sitk_img,
        size,
        reorientation: Reorientation,
        permutation: Tuple[int, int, int],
        title: str,
        axis_labels: List[str],
        mu_map=None,
        flip_axes: Tuple[bool, bool, bool] = (False, False, False),
    ):
        self.sitk_img = sitk_img
        self.mu_map = mu_map
        self.permutation = permutation
        self.flip_axes = flip_axes
        self.title = title
        self.axis_labels = axis_labels

        self.reorientation = reorientation

        _mu_map = self.transform_image(mu_map) if mu_map is not None else None
        self.slice_view_state = SliceViewState(
            sitk_image=self.transform_image(self.sitk_img),
            slice=IntState(sitk_img.GetSize()[0] // 2),
            size=size,
            mu_map=_mu_map,
        )

        reorientation.on_change(self.apply_reorientation)

    def apply_reorientation(self, state):
        _mu_map = self.transform_image(self.mu_map) if self.mu_map is not None else None
        self.slice_view_state.update(
            sitk_image=self.transform_image(self.sitk_img),
            mu_map=_mu_map,
        )

    def transform_image(self, sitk_image):
        _img = self.reorientation.apply(sitk_image[:])
        _img = sitk.PermuteAxes(_img, self.permutation)
        _img = sitk.Flip(_img, self.flip_axes)
        return _img


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
