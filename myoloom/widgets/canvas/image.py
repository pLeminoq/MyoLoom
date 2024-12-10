from typing import Optional

import cv2 as cv
import numpy as np
from PIL import ImageTk
from PIL import Image as PILImage
import tkinter as tk

from ...state import ObjectState


class ImageState(ObjectState):

    def __init__(self, value: np.ndarray):
        super().__init__(value)

        assert (
            len(self.value.shape) == 3
        ), f"Expected an RGB image with 3 dimensions, but got {len(self.value.shape)}"
        assert (
            self.value.shape[-1] == 3
        ), f"Expected the last dimensions to be color which means size 3, but got {self.value.shape[0]}"


def img_to_tk(img: np.array) -> ImageTk:
    return ImageTk.PhotoImage(PILImage.fromarray(img))


class Image:

    def __init__(self, canvas: tk.Canvas, state: ImageState):
        self.canvas = canvas
        self.state = state

        self.img_tk = img_to_tk(self.state.value)
        self.img_id = self.canvas.create_image(
            self.state.value.shape[0] // 2,
            self.state.value.shape[1] // 2,
            image=self.img_tk,
        )

        self.state.on_change(self.redraw)

    def redraw(self, state):
        self.img_tk = img_to_tk(state.value)
        self.canvas.itemconfig(self.img_id, image=self.img_tk)
