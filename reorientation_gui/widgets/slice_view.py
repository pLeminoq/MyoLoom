from typing import Optional, Tuple

import cv2 as cv
import numpy as np
import tkinter as tk
import SimpleITK as sitk

from reorientation_gui.state import State, IntState, SITKImageState
from reorientation_gui.widgets.canvas.image import Image, ImageState
from reorientation_gui.widgets.slice_selector import SliceSelector
from reorientation_gui.util import normalize_image


class SliceViewState(State):

    def __init__(self, sitk_img_state: SITKImageState, slice: IntState, size: Tuple[int, int], mu_map_img_state: SITKImageState):
        super().__init__(verify_change=False)

        self.sitk_img_state = sitk_img_state
        self.mu_map_img_state = mu_map_img_state

        self.view_3d, self.mu_map_view = self.compute_view_3d()
        self.sitk_img_state.on_change(self.update_view_3d)
        self.mu_map_img_state.on_change(self.update_view_3d)

        self.slice = slice
        self.size = size
        self.view = ImageState(self.compute_view())

    def update_view_3d(self, sitk_img_state: SITKImageState):
        self.view_3d, self.mu_map_view = self.compute_view_3d()
        self.view.update(self.compute_view())
        self.notify_change()

    def compute_view_3d(self) -> np.array:
        view = sitk.GetArrayFromImage(self.sitk_img_state.value)
        view = normalize_image(view)

        mu_map_view = sitk.GetArrayFromImage(self.mu_map_img_state.value)
        mu_map_view = normalize_image(mu_map_view, clip=0.2)

        return view, mu_map_view

    def compute_view(self) -> np.array:
        view = self.view_3d[self.slice.value]
        view = cv.applyColorMap(view, cv.COLORMAP_INFERNO)
        view = cv.cvtColor(view, cv.COLOR_BGR2RGB)

        view_mu_map = self.mu_map_view[self.slice.value]
        view_mu_map = cv.cvtColor(view_mu_map, cv.COLOR_GRAY2RGB)

        view = cv.addWeighted(view_mu_map, 0.6, view, 1.0, 0.0)
        view = cv.resize(view, self.size)
        return view

    def update(
        self,
        sitk_image: Optional[sitk.Image] = None,
        mu_map: Optional[sitk.Image] = None,
        slice: Optional[int] = None,
        size: Optional[Tuple[int, int]] = None,
    ):
        if sitk_image is not None:
            self.sitk_image = sitk_image

        if mu_map is not None:
            self.mu_map = mu_map

        if sitk_image is not None or mu_map is not None:
            self.view_3d, self.mu_map_view = self.compute_view_3d()

        self.slice.value = slice if slice is not None else self.slice.value
        self.size = size if size is not None else self.size

        self.view.update(self.compute_view())
        self.notify_change()


class SliceView(tk.Frame):

    def __init__(self, parent: tk.Frame, state: SliceViewState):
        super().__init__(parent)

        self.state = state
        self.canvas = tk.Canvas(self, width=state.size[0], height=state.size[1])
        self.image = Image(self.canvas, state.view)

        self.slice_selector = SliceSelector(
            self,
            n_slices=state.sitk_img_state.value.GetSize()[1] - 1,
            current_slice=state.slice.value,
            length=self.state.size[0] // 2,
        )

        self.slice_selector.slice_var.trace_add(
            "write",
            lambda *args: self.state.update(
                slice=self.slice_selector.slice_var.get()
            ),
        )
        self.state.slice.on_change(
            lambda state: self.slice_selector.slice_var.set(state.value)
        )

        self.canvas.grid(column=0, row=0)
        self.slice_selector.grid(column=0, row=1)
