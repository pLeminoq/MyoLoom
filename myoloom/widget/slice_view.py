import time
import tkinter as tk
from tkinter import ttk
from typing import Optional, Tuple

import cv2 as cv
import numpy as np
import SimpleITK as sitk

from reacTk.widget.canvas import Canvas, CanvasState
from reacTk.widget.canvas.image import Image, ImageData, ImageState, ImageStyle
from widget_state import (
    compute,
    computed,
    BasicState,
    HigherOrderState,
    ObjectState,
    IntState,
    FloatState,
)

from ..util import normalize_image
from .scale import Scale, ScaleState


class SITKData(BasicState[sitk.Image]):
    """
    Reactive container for an SITK image.
    """

    def __init__(self, value: sitk.Image):
        super().__init__(value, verify_change=False)


class SliceViewState(HigherOrderState):
    def __init__(
        self,
        sitk_img: SITKData,
        slice: Optional[IntState] = None,
        clip_percentage: Optional[FloatState] = None,
        colormap: Optional[IntState] = None,
    ):
        super().__init__()

        # print(f" - Init with {type(sitk_img)=}")
        self.sitk_img = (
            sitk_img if isinstance(sitk_img, SITKData) else SITKData(sitk_img)
        )
        # print(f" - Wrapped? Init with {type(sitk_img)=}")
        self.slice = (
            slice
            if slice is not None
            else IntState(self.sitk_img.value.GetSize()[2] // 2)
        )
        self.clip_percentage = (
            clip_percentage if clip_percentage is not None else FloatState(1.0)
        )
        self.colormap = colormap if colormap is not None else IntState(None)

        self._validate_computed_states()

    @computed
    def normalized_image(
        self, sitk_img: SITKData, clip_percentage: FloatState
    ) -> ImageData:
        image = sitk.GetArrayFromImage(sitk_img.value)
        if image.max() == image.min() == 0.0:
            return ImageData(np.zeros(image.shape, np.uint8))

        image = np.clip(
            image, a_min=image.min(), a_max=clip_percentage.value * image.max()
        )
        image = (image - image.min()) / (image.max() - image.min())
        image = (255 * image).astype(np.uint8)
        return ImageData(image)

    @computed
    def slice_image(
        self,
        normalized_image: ImageData,
        slice: IntState,
        colormap: IntState,
    ) -> ImageData:
        """
        Convert the SITK image to an np.array and normalize the image.
        """
        image = normalized_image.value

        try:
            slice_image = image[slice.value]
        except IndexError:
            return ImageData(np.zeros(image.shape[:2], np.uint8))

        if colormap.value is not None:
            slice_image = cv.applyColorMap(slice_image, colormap.value)
            slice_image = cv.cvtColor(slice_image, cv.COLOR_BGR2RGB)

        return ImageData(slice_image)


class SliceView(ttk.Frame):
    def __init__(self, parent: tk.Widget, state: SliceViewState):
        """
        Widget to display/view slices of a 3D image.

        The slice view consists of a canvas displaying the image as well as
        a scale/slider to select the slice of the image.
        """
        super().__init__(parent)

        self._state = state

        self.canvas = Canvas(self, CanvasState())
        self.image = Image(
            self.canvas,
            ImageState(
                state.slice_image, style=ImageStyle(fit="contain", background=True)
            ),
        )

        self.scale = Scale(
            self,
            state=ScaleState(
                value=state.slice,
                min_value=0,
                max_value=compute(
                    [state.sitk_img],
                    lambda: IntState(state.sitk_img.value.GetSize()[0] - 1),
                ),
                length=100,
                orientation=tk.HORIZONTAL,
            ),
        )

        self.canvas.bind(
            "<Configure>",
            lambda event: self.scale._state.length.set(event.width // 2),
            add=True,
        )

        self.canvas.grid(column=0, row=0, sticky="nswe")
        self.scale.grid(column=0, row=1)

        self.rowconfigure(0, weight=9, minsize=256)
        self.rowconfigure(1, weight=1)
        self.columnconfigure(0, weight=1, minsize=256)
