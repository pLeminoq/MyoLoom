from dataclasses import dataclass
from typing import Optional, Tuple

import cv2 as cv
import numpy as np
from PIL import Image, ImageTk
import SimpleITK as sitk
import tkinter as tk
from tkinter import ttk

from reorientation_gui.slice_selector import SliceSelector
from reorientation_gui.state.reorientation import ReorientationState
from reorientation_gui.transformation_canvas import ReorientationCanvas

"""
RotationGUI: ReorientationCanvas + Canvas zum Anzeigen der Transformation + Slice
2te RotationGUI die aus einer andere Perspektive drauf schaut?
"""

# TODO: Umrechnung von Centerpoint des ReorientationCanvas basierend auf canvas resolution und Bildauflösung
# TODO: initialen slice basierend auf der maximalen Aktivität (in zentraler Region des Bildes) auswählen?
# TODO: GesamtErgebnis in eigenem Canvas anzeigen


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
    image: sitk.Image
    transformation: ReorientationState


class ReorienationResultCanvas(tk.Canvas):

    def __init__(
        self,
        parent: tk.Frame,
        image: ImageTk,
        width: int = 512,
        height: int = 512,
        line_color: str = "green",
        dash: Tuple[int, int] = (8, 8),
    ):
        super().__init__(parent, width=width, height=height)

        self.image = image
        self.width = width
        self.height = height
        self.line_color = line_color
        self.dash = dash

        self.id_img = self.create_image(
            self.width // 2, self.height // 2, image=self.image
        )
        self.id_line_h = self.create_line(
            (0, self.height // 2),
            (self.width, self.height // 2),
            fill=line_color,
            dash=self.dash,
        )
        self.id_line_v = self.create_line(
            (self.width // 2, 0),
            (self.width // 2, self.height),
            fill=line_color,
            dash=self.dash,
        )

    def update_image(self, image: ImageTk):
        self.image = image
        self.itemconfig(self.id_img, image=self.image)


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
        self.canvas_res = ReorienationResultCanvas(
            self,
            image=sitk_to_tk(
                self.state.transformation.apply(),
                _slice=self.slice_selector.slice_var.get(),
            ),
        )

        # handle reactivity
        ## update transformation based on reorientation_canvas
        self.reorientation_canvas.state.on_change(lambda *args: self.update_transformation())
        ## update image on slice change
        self.slice_selector.slice_var.trace_add("write", self.redraw_images)
        ## update image on transformation change
        self.state.transformation.on_change(
            self.on_transformation_change
        )  # TODO: the points of the reorientation canvas may also require an update

        self.update_transformation()

        self.reorientation_canvas.grid(column=0, row=0)
        self.canvas_res.grid(column=1, row=0)
        self.slice_selector.grid(column=0, row=1, columnspan=2)
        # self.canvas.on_change(t_callback)

    def redraw_images(self, *args):
        self.reorientation_canvas.update_img(
            sitk_to_tk(self.state.image, _slice=self.slice_selector.slice_var.get())
        )
        self.canvas_res.update_image(
            sitk_to_tk(
                self.state.transformation.apply(translation="xy", rotation="z"),
                _slice=self.slice_selector.slice_var.get(),
            )
        )

    def update_transformation(self, *args):
        self.state.transformation.update(
            angle_z=np.pi / 2.0 - self.reorientation_canvas.state.angle,
            heart_x=round(self.reorientation_canvas.state.p_center.x / 4),
            heart_y=round(self.reorientation_canvas.state.p_center.y / 4),
        )

    def on_transformation_change(self, state):
        heart_center = state.center_heart

        self.reorientation_canvas.state.p_center.update(x=heart_center[0] * 4, y=heart_center[1] * 4, notify=False)
        self.reorientation_canvas.redraw_p_center()



class SideView(tk.Frame):
    def __init__(self, parent: tk.Frame, state: State):
        super().__init__(parent)

        self.state = state

        def perm(sitk_image):
            return sitk.PermuteAxes(sitk_image, (2, 1, 0))

        self.perm = perm

        self.slice_selector = SliceSelector(
            self,
            n_slices=self.state.image.GetSize()[2] - 1,
            # current_slice=self.state.image.GetSize()[2] // 2,
            current_slice=74,
            length=256,
        )

        self.reorientation_canvas = ReorientationCanvas(
            self,
            img=sitk_to_tk(
                self.perm(self.state.image), _slice=self.slice_selector.slice_var.get()
            ),
        )
        self.canvas_res = ReorienationResultCanvas(
            self,
            image=sitk_to_tk(
                self.perm(self.state.transformation.apply()),
                _slice=self.slice_selector.slice_var.get(),
            ),
        )

        # handle reactivity
        ## update transformation based on reorientation_canvas
        self.reorientation_canvas.state.on_change(lambda *args: self.update_transformation())
        ## update image on slice change
        self.slice_selector.slice_var.trace_add("write", self.redraw_images)
        ## update image on transformation change
        self.state.transformation.on_change(
            self.redraw_images
        )  # TODO: the points of the reorientation canvas may also require an update

        self.update_transformation()

        self.reorientation_canvas.grid(column=0, row=0)
        self.canvas_res.grid(column=1, row=0)
        self.slice_selector.grid(column=0, row=1, columnspan=2)
        # self.canvas.on_change(t_callback)

    def redraw_images(self, *args):
        self.reorientation_canvas.update_img(
            sitk_to_tk(
                self.perm(self.state.image), _slice=self.slice_selector.slice_var.get()
            )
        )
        self.canvas_res.update_image(
            sitk_to_tk(
                self.perm(
                    self.state.transformation.apply(translation="zy", rotation="x")
                ),
                _slice=self.slice_selector.slice_var.get(),
            )
        )

    def update_transformation(self, *args):
        self.state.transformation.update(
            angle_x=self.reorientation_canvas.state.angle,
            heart_y=round(self.reorientation_canvas.state.p_center[1] / 4),
            heart_z=round(self.reorientation_canvas.state.p_center[0] / 4),
        )


class RotationGUI(tk.Tk):
    def __init__(self, sitk_img: sitk.Image):
        super().__init__()

        state = State(
            image=sitk_img,
            transformation=ReorientationState(sitk_img),
        )
        print(state.transformation)

        self.view_transversal = TransversalView(self, state)
        self.view_side = SideView(self, state)

        perm_f = lambda x: sitk.PermuteAxes(x, (1, 2, 0))

        # self.slice_selector = SliceSelector(
            # self,
            # n_slices=state.image.GetSize()[1] - 1,
            # # current_slice=self.state.image.GetSize()[2] // 2,
            # current_slice=64,
            # length=256,
        # )
        # self.canvas_result = ReorienationResultCanvas(
            # self,
            # image=sitk_to_tk(
                # perm_f(state.transformation.apply()),
                # _slice=self.slice_selector.slice_var.get(),
            # ),
        # )

        # def on_slice_change(*arsg):
            # print(f"Updaet imge?")
            # self.canvas_result.update_image(
                # sitk_to_tk(
                    # perm_f(state.transformation.apply()),
                    # _slice=self.slice_selector.slice_var.get(),
                # )
            # )
        # self.slice_selector.slice_var.trace_add("write", on_slice_change)

        self.view_transversal.grid(column=0, row=0)
        self.view_side.grid(column=0, row=1)

        # self.canvas_result.grid(column=1, row=0, rowspan=1)
        # self.slice_selector.grid(column=1, row=1, rowspan=1)

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
    # print(sitk_img.GetSize())
    sitk_img = sitk.ConstantPad(sitk_img, (0, 0, 44), (0, 0, 43), 0.0)
    sitk_img.SetOrigin((0, 0, 0))
    sitk_img.SetDirection((1, 0, 0, 0, 1, 0, 0, 0, 1))
    # sitk_img = sitk.PermuteAxes(sitk_img, (2, 1, 0))
    # print(sitk_img.GetSize())
    pt = (64, 64, 64)
    print(f"{pt} -> {sitk_img.TransformIndexToPhysicalPoint(pt)} -> {sitk_img.TransformPhysicalPointToIndex(sitk_img.TransformIndexToPhysicalPoint(pt))}")
    pt = (64, 64, 0)
    print(f"{pt} -> {sitk_img.TransformIndexToPhysicalPoint(pt)} -> {sitk_img.TransformPhysicalPointToIndex(sitk_img.TransformIndexToPhysicalPoint(pt))}")

    # ctr = (64, 64, 64)
    # ctr_phy = sitk_img.TransformIndexToPhysicalPoint(ctr)
    # print(sitk_img.GetOrigin())
    # print(ctr, ctr_phy)

    app = RotationGUI(sitk_img)
    app.mainloop()
