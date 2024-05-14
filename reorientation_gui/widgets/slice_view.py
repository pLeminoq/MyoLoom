from typing import Optional, Tuple

import cv2 as cv
import numpy as np
import tkinter as tk
import SimpleITK as sitk

from reorientation_gui.widgets.canvas.image import Image, ImageState
from reorientation_gui.widgets.scale import Scale, ScaleState
from reorientation_gui.util import normalize_image

from reorientation_gui.state import (
    HigherState,
    ObjectState,
    IntState,
    FloatState,
    SequenceState,
    computed_state,
    ResolutionState,
)


class SliceViewState(HigherState):

    def __init__(
        self,
        sitk_img_state: ObjectState,
        slice_state: IntState,
        resolution_state: ResolutionState,
        normalization_state: FloatState,
    ):
        super().__init__()

        self.sitk_img_state = sitk_img_state
        self.slice_state = slice_state
        self.resolution_state = resolution_state
        self.normalization_state = normalization_state

        self.view_state = self.view_state(self.sitk_img_state, self.normalization_state)
        self.slice_view_state = self.slice_view_state(
            self.view_state, self.slice_state, self.resolution_state
        )

    @computed_state
    def view_state(
        self, sitk_img_state: ObjectState, normalization_state: FloatState
    ) -> ObjectState:
        view = sitk.GetArrayFromImage(sitk_img_state.value)
        view = normalize_image(view, clip=view.max() * normalization_state.value)
        return ObjectState(view)

    @computed_state
    def slice_view_state(
        self,
        view_state: ObjectState,
        slice_state: IntState,
        resolution_state: ResolutionState,
    ) -> ObjectState:
        slice_view = view_state.value[slice_state.value]
        slice_view = cv.applyColorMap(slice_view, cv.COLORMAP_INFERNO)
        slice_view = cv.cvtColor(slice_view, cv.COLOR_BGR2RGB)
        slice_view = cv.resize(slice_view, self.resolution_state.values())
        return ObjectState(slice_view)


class SliceView(tk.Frame):

    def __init__(self, parent: tk.Frame, state: SliceViewState):
        super().__init__(parent)

        self.state = state
        self.canvas = tk.Canvas(
            self,
            width=state.resolution_state.width.value,
            height=state.resolution_state.height.value,
        )
        self.image = Image(self.canvas, state.slice_view_state)

        self.slice_scale = Scale(
            self,
            state=ScaleState(
                number_state=self.state.slice_state,
                value_range=(0, self.state.sitk_img_state.value.GetSize()[0] - 1),
                length=self.state.resolution_state.width.value // 2,
            ),
        )

        self.canvas.grid(column=0, row=0)
        self.slice_scale.grid(column=0, row=1)
