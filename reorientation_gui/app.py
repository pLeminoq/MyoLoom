from dataclasses import dataclass
from typing import Optional, Tuple

import cv2 as cv
import numpy as np
from PIL import Image, ImageTk
import SimpleITK as sitk
import tkinter as tk
from tkinter import ttk

from reorientation_gui.slice_selector import SliceSelector
from reorientation_gui.transformation_canvas import ReorientationCanvas

"""
RotationGUI: ReorientationCanvas + Canvas zum Anzeigen der Transformation + Slice
2te RotationGUI die aus einer andere Perspektive drauf schaut?
"""


class Transformation:
    def __init__(self, angle_z, heart_center):
        self.angle_z = angle_z
        self.angle_y = 0.0
        self.angle_x = 0.0
        self.heart_center = heart_center
        self.callbacks = []

    def to_sitk(self, sitk_img):
        _size = sitk_img.GetSize()
        _slice = self.heart_center[2]

        hrt_ctr = (
            self.heart_center[0] // 4,
            self.heart_center[1] // 4,
            self.heart_center[2],
        )
        # print(hrt_ctr, (_slice, _size[1] // 2, _size[0] // 2))

        p_ctr_img = np.array(
            sitk_img.TransformIndexToPhysicalPoint(
                (_slice, _size[1] // 2, _size[0] // 2)
            )
        )[::-1]
        p_ctr_heart = np.array(sitk_img.TransformIndexToPhysicalPoint(hrt_ctr[::-1]))[
            ::-1
        ]
        # offset = p_ctr_img - p_ctr_heart
        offset = p_ctr_heart - p_ctr_img

        translation = sitk.TranslationTransform(3, (offset[1], offset[0], offset[2]))
        rotation = sitk.Euler3DTransform(
            p_ctr_img, 0.0, 0.0, np.pi / 2.0 - self.angle_z
        )
        return sitk.CompositeTransform([translation, rotation])

    def update(self, angle_z=None, angle_y=None, angle_x=None, heart_center=None):
        self.angle_z = angle_z if angle_z is not None else self.angle_z
        self.angle_y = angle_y if angle_y is not None else self.angle_y
        self.angle_x = angle_x if angle_x is not None else self.angle_x
        self.heart_center = (
            heart_center if heart_center is not None else self.heart_center
        )

        for callback in self.callbacks:
            callback(self)

    def on_change(self, callback):
        self.callbacks.append(callback)


class ImageData:
    def init(self, sitk_image: sitk.Image):
        # TODO: square padding

        self.sitk_image = sitk_image
        # self.image =

        pass


def sitk_to_tk(
    sitk_image: sitk.Image,
    _slice: Optional[int] = None,
    resolution: Tuple[int, int] = (512, 512),
):
    img = sitk.GetArrayFromImage(sitk_image)
    img = (img - img.min()) / (img.max() - img.min())
    img = (255 * img).astype(np.uint8)

    if _slice is None:
        _slice = img.shape[0] // 2

    img = img[_slice]
    img = cv.resize(img, resolution)

    img_tk = ImageTk.PhotoImage(Image.fromarray(img))
    return img_tk


@dataclass
class State:
    # TODO: allow to query transformed image
    image: sitk.Image
    transformation: Transformation

    def get_reoriented_image(self):
        # copy image so that original is not modified
        image_t = self.image[:]

        # treat original as base: add translation and rotation
        image_t.SetOrigin((0.0, 0.0, 0.0))
        image_t.SetDirection((1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0))

        # apply transformation
        image_t = sitk.Resample(
            image_t,
            image_t,
            self.transformation.to_sitk(image_t),
            sitk.sitkLinear,
            0.0,
        )
        return image_t


class TransversalView(tk.Frame):
    def __init__(self, parent: tk.Frame, state: State):
        super().__init__(parent)

        self.state = state

        self.slice_selector = SliceSelector(
            self,
            n_slices=self.state.image.GetSize()[2] - 1,
            current_slice=self.state.image.GetSize()[2] // 2,
            length=256,
        )

        self.reorientation_canvas = ReorientationCanvas(
            self,
            img=sitk_to_tk(
                self.state.image, _slice=self.slice_selector.slice_var.get()
            ),
        )

        self.img_ref = sitk_to_tk(self.state.get_reoriented_image())
        self.result_canvas = tk.Canvas(self, width=512, height=512)
        self.img_id = self.result_canvas.create_image(256, 256, image=self.img_ref)

        # handle reactivity
        ## update transformation based on reorientation_canvas
        self.reorientation_canvas.on_change(self.update_transformation)
        ## update image on slice change
        self.slice_selector.slice_var.trace_add("write", self.redraw_images)
        ## update image on transformation change
        self.state.transformation.on_change(
            self.redraw_images
        )  # TODO: the points of the reorientation canvas may also require an update

        self.update_transformation()

        self.reorientation_canvas.grid(column=0, row=0)
        self.result_canvas.grid(column=1, row=0)
        self.slice_selector.grid(column=0, row=1, columnspan=2)
        # self.canvas.on_change(t_callback)

    def redraw_images(self, *args):
        self.reorientation_canvas.update_img(
            sitk_to_tk(self.state.image, _slice=self.slice_selector.slice_var.get())
        )

        self.img_ref = sitk_to_tk(
            self.state.get_reoriented_image(),
            _slice=self.slice_selector.slice_var.get(),
        )
        self.result_canvas.itemconfig(self.img_id, image=self.img_ref)

    def update_transformation(self, *args):
        self.state.transformation.update(
            angle_z=self.reorientation_canvas.angle,
            heart_center=[
                *self.reorientation_canvas.p_center[::-1],
                self.state.transformation.heart_center[2],
            ],
        )


class RotationGUI(tk.Tk):
    def __init__(self, sitk_img: sitk.Image):
        super().__init__()

        state = State(
            image=sitk_img,
            transformation=Transformation(angle_z=0.0, heart_center=(64, 64, 64)),
        )

        self.view_transversal = TransversalView(self, state)

        self.view_transversal.grid(column=0, row=0)

        self.bind("<Key-q>", lambda event: exit(0))
        ttk.Style().theme_use("clam")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="GUI to center and rotate a SPECT image into short-axis view",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--file",
        type=str,
        default="data/multi-center/Bad Oeynhausen/0010-recon_nac_nsc.dcm",
    )
    args = parser.parse_args()

    sitk_reader = sitk.ImageFileReader()
    sitk_reader.SetFileName(args.file)
    sitk_img = sitk_reader.Execute()
    sitk_img = sitk.ConstantPad(sitk_img, (0, 0, 44), (0, 0, 43), 0.0)
    # sitk_img = sitk.PermuteAxes(sitk_img, (2, 1, 0))

    app = RotationGUI(sitk_img)
    app.mainloop()
