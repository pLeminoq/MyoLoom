from typing import Optional

import cv2 as cv
import numpy as np
import tkinter as tk

from reorientation_gui.state import State
from reorientation_gui.util import img_to_tk


class ImageState(State):

    def __init__(self, image: np.array):
        super().__init__(verify_change=False)

        assert len(image.shape) == 3, f"Expected an RGB image with 3 dimensions, but got {len(image.shape)}"
        assert image.shape[-1] == 3, f"Expected the last dimensions to be color which means size 3, but got {image.shape[0]}"

        self.image = image

    def update(self, image: np.array):
        assert self.image.shape == image.shape, f"Got update with a different image shape. Expected {self.image.shape}, but got {image.shape}"
        self.image = image
        self.notify_change()


class Image:

    def __init__(self, canvas: tk.Canvas, state: ImageState):
        self.canvas = canvas
        self.state = state

        self.img_tk = img_to_tk(self.state.image)
        self.img_id = self.canvas.create_image(
            state.image.shape[0] // 2, state.image.shape[1] // 2, image=self.img_tk
        )

        self.state.on_change(self.redraw)

    def redraw(self, state):
        self.img_tk = img_to_tk(state.image)
        self.canvas.itemconfig(self.img_id, image=self.img_tk)
