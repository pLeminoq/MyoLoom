import numpy as np
import SimpleITK as sitk
import tkinter as tk
from tkinter import ttk

from reorientation_gui.state import Point, Reorientation, IntState, FloatState
from reorientation_gui.widgets.slice_view import SliceView, SliceViewState
from reorientation_gui.widgets.canvas import RectangleState
from reorientation_gui.widgets.slice_selector import SliceSelector
from reorientation_gui.widgets.reorientation_view import (
    ReorientationView,
    ReorientationViewState,
)
from reorientation_gui.widgets.menu import MenuBar
from reorientation_gui.widgets.result_view import ResultView, ResultViewState

# ToDo's
# Debuggen, dass Result anzeige richtig
#  * Open - File Dialog at startup
#  * FileDialog modifes AppState


class App(tk.Tk):

    def __init__(self, sitk_img, mu_map=None):
        super().__init__()

        reorientation = Reorientation(
            angle_x=0.0,
            angle_y=0.0,
            angle_z=0.0,
            center_x=sitk_img.GetSize()[0] // 2,
            center_y=sitk_img.GetSize()[1] // 2,
            center_z=sitk_img.GetSize()[2] // 2,
        )

        size = (400, 400)

        scale = size[0] / sitk_img.GetSize()[0]
        to_image_scale = lambda value: round(value / scale)
        to_visual_scale = lambda value: round(value * scale)

        self.menu_bar = MenuBar(self)

        self.frame_reorie = tk.Frame(self, highlightthickness=2, highlightbackground="black")
        self.view_trans = ReorientationView(
            self.frame_reorie,
            ReorientationViewState(
                slice_view=SliceViewState(
                    sitk_img, reorientation.center_z, size=size, mu_map=mu_map
                ),
                rect_center=RectangleState(
                    center=Point(
                        reorientation.center_x.create_t(
                            to_visual_scale, to_image_scale
                        ),
                        reorientation.center_y.create_t(
                            to_visual_scale, to_image_scale
                        ),
                    ),
                    size=5,
                    color="green",
                ),
                angle=reorientation.angle_z,
                distance=30,
                rect_angle_color="blue",
                line_color="black",
                title="Transversal",
            ),
        )

        self.view_sagittal = ReorientationView(
            self.frame_reorie,
            ReorientationViewState(
                slice_view=SliceViewState(
                    sitk_image=sitk.PermuteAxes(sitk_img, (1, 2, 0)),
                    slice=IntState(64),
                    size=size,
                    mu_map=sitk.PermuteAxes(mu_map[:], (1, 2, 0)) if mu_map is not None else None,
                ),
                rect_center=RectangleState(
                    center=Point(
                        x=IntState(size[0] // 2),
                        y=IntState(size[1] // 2),
                    ),
                    size=5,
                    color="green",
                ),
                angle=reorientation.angle_y,
                distance=30,
                rect_angle_color="blue",
                line_color="black",
                title="Saggital",
                verticle=False,
            ),
        )

        self.hla = ResultView(
            self,
            ResultViewState(
                sitk_img=sitk_img,
                size=size,
                reorientation=reorientation,
                permutation=(0, 1, 2),
                title="Horizontal Long Axis (HLA)",
                axis_labels=["Apex", "Septal", "Lateral", "Basis"],
                mu_map=mu_map,
            ),
        )
        self.sa = ResultView(
            self,
            ResultViewState(
                sitk_img=sitk_img,
                size=size,
                reorientation=reorientation,
                permutation=(2, 0, 1),
                title="Short Axis (SA)",
                axis_labels=["Anterior", "Septal", "Lateral", "Inferior"],
                mu_map=mu_map,
                flip_axes=(True, False, False),
            ),
        )
        self.vla = ResultView(
            self,
            ResultViewState(
                sitk_img=sitk_img,
                size=size,
                reorientation=reorientation,
                permutation=(1, 2, 0),
                title="Vertical Long Axis (VLA)",
                axis_labels=["Anterior", "Basis", "Apex", "Inferior"],
                mu_map=mu_map,
                flip_axes=(True, True, False),
            ),
        )

        self.view_trans.grid(column=0, row=0, padx=40, pady=5)
        self.view_sagittal.grid(column=0, row=1, padx=40, pady=5)
        self.frame_reorie.grid(column=0, row=0, rowspan=2, padx=10, pady=5)

        self.hla.grid(column=1, row=0)
        self.sa.grid(column=1, row=1)
        self.vla.grid(column=2, row=1)

        self.bind("<Key-q>", lambda event: exit(0))
        ttk.Style().theme_use("clam")


if __name__ == "__main__":
    filename = "../dlac/data/second/images/0002-stress-recon_nac_nsc.dcm"
    filename_mm = "../dlac/data/second/images/0002-stress-mu_map.dcm"

    sitk_reader = sitk.ImageFileReader()
    sitk_reader.SetFileName(filename)
    sitk_img = sitk_reader.Execute()
    sitk_img = sitk.ConstantPad(sitk_img, (0, 0, 44), (0, 0, 43), 0.0)

    sitk_reader.SetFileName(filename_mm)
    mu_map = sitk_reader.Execute()
    mu_map = sitk.ConstantPad(mu_map, (0, 0, 48), (0, 0, 47), 0.0)

    app = App(sitk_img, mu_map)
    # app = App(sitk_img)
    app.mainloop()
