import numpy as np
import SimpleITK as sitk
import tkinter as tk
from tkinter import ttk

from reorientation_gui.state import (
    Point,
    ReorientationState,
    IntState,
    FloatState,
    State,
    StringState,
    FileImageState,
    TransformedSITKImageState,
)
from reorientation_gui.state import AppState
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
# Reset Points in ReorientationView if new image is loaded
# Replace mu map with according sitk_img_state
# save reorientation to csv: serialize app state as row with values [filename, angle_x, angle_y, angle_z, ]


class App(tk.Tk):

    def __init__(self, app_state: AppState):
        super().__init__()

        size = (512, 512)
        mu_map = app_state.file_image_state_mu_map.sitk_img_state.value
        rect_size=10

        scale = (
            size[0] / app_state.file_image_state_spect.sitk_img_state.value.GetSize()[0]
        )
        to_image_scale = lambda value: round(value / scale)
        to_visual_scale = lambda value: round(value * scale)

        self.menu_bar = MenuBar(self, app_state)

        self.frame_reorie = tk.Frame(
            self, highlightthickness=2, highlightbackground="black"
        )
        self.view_trans = ReorientationView(
            self.frame_reorie,
            ReorientationViewState(
                slice_view=SliceViewState(
                    sitk_img_state=TransformedSITKImageState(
                        _sitk_img_state=app_state.file_image_state_spect.sitk_img_state,
                    ),
                    slice=app_state.reorientation_state.center_z,
                    size=size,
                    mu_map=mu_map,
                ),
                rect_center=RectangleState(
                    center=Point(
                        app_state.reorientation_state.center_x.create_t(
                            to_visual_scale, to_image_scale
                        ),
                        app_state.reorientation_state.center_y.create_t(
                            to_visual_scale, to_image_scale
                        ),
                    ),
                    size=rect_size,
                    color="green",
                ),
                angle=app_state.reorientation_state.angle_z,
                distance=30,
                rect_angle_color="blue",
                line_color="white",
                title="Transversal",
            ),
        )

        self.view_sagittal = ReorientationView(
            self.frame_reorie,
            ReorientationViewState(
                slice_view=SliceViewState(
                    sitk_img_state=TransformedSITKImageState(
                        _sitk_img_state=app_state.file_image_state_spect.sitk_img_state,
                        permutation=(1, 2, 0),
                    ),
                    slice=IntState(64),
                    size=size,
                    mu_map=(
                        sitk.PermuteAxes(mu_map[:], (1, 2, 0))
                        if mu_map is not None
                        else None
                    ),
                ),
                rect_center=RectangleState(
                    center=Point(
                        x=IntState(size[0] // 2),
                        y=IntState(size[1] // 2),
                    ),
                    size=rect_size,
                    color="green",
                ),
                angle=app_state.reorientation_state.angle_y,
                distance=30,
                rect_angle_color="blue",
                line_color="white",
                title="Saggital",
                verticle=False,
            ),
        )

        self.hla = ResultView(
            self,
            ResultViewState(
                sitk_img_state=TransformedSITKImageState(
                    app_state.file_image_state_spect.sitk_img_state,
                    reorientation_state=app_state.reorientation_state,
                ),
                size=size,
                title="Horizontal Long Axis (HLA)",
                axis_labels=["Apex", "Septal", "Lateral", "Basis"],
                mu_map=mu_map,
            ),
        )
        self.sa = ResultView(
            self,
            ResultViewState(
                sitk_img_state=TransformedSITKImageState(
                    app_state.file_image_state_spect.sitk_img_state,
                    reorientation_state=app_state.reorientation_state,
                    permutation=(2, 0, 1),
                    flip_axes=(True, False, False),
                ),
                size=size,
                title="Short Axis (SA)",
                axis_labels=["Anterior", "Septal", "Lateral", "Inferior"],
                mu_map=mu_map,
            ),
        )
        self.vla = ResultView(
            self,
            ResultViewState(
                sitk_img_state=TransformedSITKImageState(
                    app_state.file_image_state_spect.sitk_img_state,
                    reorientation_state=app_state.reorientation_state,
                    permutation=(1, 2, 0),
                    flip_axes=(True, True, False),
                ),
                size=size,
                title="Vertical Long Axis (VLA)",
                axis_labels=["Anterior", "Basis", "Apex", "Inferior"],
                mu_map=mu_map,
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
    from reorientation_gui.util import load_image, square_pad
    from reorientation_gui.widgets.file_dialog import FileDialog


    app_state = AppState()

    # dialog = FileDialog(app_state)
    # dialog.grab_set()
    # dialog.wait_window()

    app_state.file_image_state_spect.filename.value = (
        "data/mpi_spect_reorientation/0001-recon.dcm"
    )

    # app = App(sitk_img, mu_map)
    app = App(app_state)
    app.mainloop()
