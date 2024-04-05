from typing import Dict, Tuple

from PIL import Image, ImageTk
import tkinter as tk


class VolumeCanvas(tk.Canvas):
    def __init__(
        self,
        parent: tk.Frame,
        image: np.ndarray,
        slice_var: tk.IntVar,
        axis_conf: Dict[str, int] = {"x": 2, "y": 1, "z": 0},
        resolution: Tuple[int, int] = (512, 512),
    ):
        super().__init__(parent)

        # TODO: assert image dtype is np.uint8

        self.image = image
        self.slice_var = slice_var
        self.axis_conf = axis_conf
        self.resolution = resolution

        self.image_ref = None

    def _draw(self):
        _image = self.image[self.slice_var.get()]
        _image = cv.resize(self.image, self.resolution)
        _image = 
        self.image_ref = ImageTk.PhotoImage(Image.fromarray(_image))

