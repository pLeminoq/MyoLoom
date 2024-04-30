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


class App(tk.Tk):

    def __init__(self, app_state: AppState):
        super().__init__()

        self.title("MPI SPECT Reorientation")

        #TODO: these parameters should be part of the app state
        _size = (self.winfo_screenheight() - 350) // 2
        rect_size = round(_size * 0.02)
        size = (_size, _size)

        scale = (
            size[0] / app_state.file_image_state_spect.sitk_img_state.value.GetSize()[0]
        )
        to_image_scale = lambda value: round(value / scale)
        to_visual_scale = lambda value: round(value * scale)

        self.menu_bar = MenuBar(self, app_state)

        self.frame_reorie = tk.Frame(
            self, highlightthickness=1, highlightbackground="black"
        )
        self.view_trans = ReorientationView(
            self.frame_reorie,
            ReorientationViewState(
                slice_view=SliceViewState(
                    sitk_img_state=TransformedSITKImageState(
                        _sitk_img_state=app_state.file_image_state_spect.sitk_img_state,
                    ),
                    mu_map_img_state=TransformedSITKImageState(
                        _sitk_img_state=app_state.file_image_state_mu_map.sitk_img_state
                    ),
                    slice=app_state.reorientation_state.center_z,
                    size=size,
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
                    mu_map_img_state=TransformedSITKImageState(
                        _sitk_img_state=app_state.file_image_state_mu_map.sitk_img_state,
                        permutation=(1, 2, 0),
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

        self.frame_result = tk.Frame(
            self, highlightthickness=1, highlightbackground="black"
        )
        self.hla = ResultView(
            self.frame_result,
            ResultViewState(
                sitk_img_state=TransformedSITKImageState(
                    app_state.file_image_state_spect.sitk_img_state,
                    reorientation_state=app_state.reorientation_state,
                ),
                mu_map_img_state=TransformedSITKImageState(
                    _sitk_img_state=app_state.file_image_state_mu_map.sitk_img_state,
                    reorientation_state=app_state.reorientation_state,
                ),
                size=size,
                title="Horizontal Long Axis (HLA)",
                axis_labels=["Apex", "Septal", "Lateral", "Basis"],
            ),
        )
        self.sa = ResultView(
            self.frame_result,
            ResultViewState(
                sitk_img_state=TransformedSITKImageState(
                    app_state.file_image_state_spect.sitk_img_state,
                    reorientation_state=app_state.reorientation_state,
                    permutation=(2, 0, 1),
                    flip_axes=(True, False, False),
                ),
                mu_map_img_state=TransformedSITKImageState(
                    _sitk_img_state=app_state.file_image_state_mu_map.sitk_img_state,
                    reorientation_state=app_state.reorientation_state,
                    permutation=(2, 0, 1),
                    flip_axes=(True, False, False),
                ),
                size=size,
                title="Short Axis (SA)",
                axis_labels=["Anterior", "Septal", "Lateral", "Inferior"],
            ),
        )
        self.vla = ResultView(
            self.frame_result,
            ResultViewState(
                sitk_img_state=TransformedSITKImageState(
                    app_state.file_image_state_spect.sitk_img_state,
                    reorientation_state=app_state.reorientation_state,
                    permutation=(1, 2, 0),
                    flip_axes=(True, True, False),
                ),
                mu_map_img_state=(
                    TransformedSITKImageState(
                        _sitk_img_state=app_state.file_image_state_mu_map.sitk_img_state,
                        reorientation_state=app_state.reorientation_state,
                        permutation=(1, 2, 0),
                        flip_axes=(True, True, False),
                    )
                ),
                size=size,
                title="Vertical Long Axis (VLA)",
                axis_labels=["Anterior", "Basis", "Apex", "Inferior"],
            ),
        )

        self.view_trans.grid(column=0, row=0, padx=20, pady=5)
        self.view_sagittal.grid(column=0, row=1, padx=20, pady=5)
        self.frame_reorie.grid(column=0, row=0, rowspan=2, padx=5, pady=5)

        self.hla.grid(column=0, row=0, padx=(20, 5), pady=5)
        self.sa.grid(column=0, row=1, padx=(20, 5), pady=5)
        self.vla.grid(column=1, row=1, padx=(5, 20), pady=5)
        self.frame_result.grid(column=1, row=0, rowspan=2, padx=5, pady=5)

        self.bind("<Key-q>", lambda event: exit(0))
        ttk.Style().theme_use("clam")

