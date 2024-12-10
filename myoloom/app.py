import numpy as np
import SimpleITK as sitk
import tkinter as tk
from tkinter import ttk

from .state import *
from .widgets import *


class App(tk.Tk):
    """
    App for MPI SPECT reorientation.

    The app shows the input image in transversal and saggital view.
    There, the user may specify the heart center and rotation angles in x and z direction.
    The result of the reorientation is display in 3 views: horizontal-long-axis, vertical-long-axis and short axis view.
    Normalization of SPECT images can be configured with a slider.
    """

    def __init__(self, state: AppState):
        super().__init__()

        self.title("MPI SPECT Reorientation")
        self.state = state

        display_resolution = (self.winfo_screenheight() - 350) // 2
        self.state.resolution_state.set(display_resolution, display_resolution)
        self.state.rectangle_size_state.value = round(display_resolution * 0.02)

        _scale = display_resolution / self.state.sitk_img_state.value.GetSize()[0]
        _to_image_scale = lambda value: round(value / _scale)
        _to_display_scale = lambda value: round(value * _scale)

        self.menu_bar = MenuBar(self, self.state)

        self.normalization_scale = Scale(
            self,
            state=ScaleState(
                number_state=self.state.normalization_state,
                value_range=(1.0, 0.0),
                length=round(1.5 * display_resolution),
                orientation=tk.VERTICAL,
                formatter=lambda x: f"{str(round(100 * x)):>3}%",
            ),
        )

        self.frame_reorie = tk.Frame(
            self, highlightthickness=1, highlightbackground="black"
        )
        self.view_trans = ReorientationView(
            self.frame_reorie,
            ReorientationViewState(
                slice_view_state=SliceViewState(
                    sitk_img_state=self.state.sitk_img_state,
                    slice_state=self.state.reorientation_state.center_state.z,
                    resolution_state=self.state.resolution_state,
                    normalization_state=self.state.normalization_state,
                ),
                rect_center_state=RectangleState(
                    center_state=PointState(
                        x=self.state.reorientation_state.center_state.x.create_transformed_state(
                            _to_display_scale, _to_image_scale
                        ),
                        y=self.state.reorientation_state.center_state.y.create_transformed_state(
                            _to_display_scale, _to_image_scale
                        ),
                    ),
                    size_state=self.state.rectangle_size_state,
                    color_state="green",
                ),
                angle_state=self.state.reorientation_state.angle_state.z,
                distance_state=30.0,
                title_state="Transversal",
                start_angle=np.deg2rad(270),
            ),
        )

        self.view_sagittal = ReorientationView(
            self.frame_reorie,
            ReorientationViewState(
                slice_view_state=SliceViewState(
                    sitk_img_state=self.state.sitk_img_saggital_state,
                    slice_state=self.state.reorientation_state.center_state.x,
                    resolution_state=self.state.resolution_state,
                    normalization_state=self.state.normalization_state,
                ),
                rect_center_state=RectangleState(
                    center_state=PointState(
                        x=self.state.reorientation_state.center_state.y.create_transformed_state(
                            _to_display_scale, _to_image_scale
                        ),
                        y=self.state.reorientation_state.center_state.z.create_transformed_state(
                            _to_display_scale, _to_image_scale
                        ),
                    ),
                    size_state=self.state.rectangle_size_state,
                    color_state="green",
                ),
                angle_state=self.state.reorientation_state.angle_state.x,
                distance_state=30.0,
                title_state="Saggital",
                start_angle=np.deg2rad(180),
            ),
        )

        self.frame_result = tk.Frame(
            self, highlightthickness=1, highlightbackground="black"
        )

        self.hla = ResultView(
            self.frame_result,
            ResultViewState(
                title="Horizontal Long Axis (HLA)",
                axis_labels=AxisLabelState("Apex", "Septal", "Lateral", "Basis"),
                slice_view_state=SliceViewState(
                    sitk_img_state=self.state.img_hla_state,
                    slice_state=0, # this will be set to the image center in the init of ResultViewState
                    resolution_state=self.state.resolution_state,
                    normalization_state=self.state.normalization_state,
                ),
            ),
        )
        self.sa = ResultView(
            self.frame_result,
            ResultViewState(
                title="Short Axis (SA)",
                axis_labels=AxisLabelState("Septal", "Anterior", "Inferior", "Lateral"),
                slice_view_state=SliceViewState(
                    sitk_img_state=self.state.img_sa_state,
                    slice_state=0, # this will be set to the image center in the init of ResultViewState
                    resolution_state=self.state.resolution_state,
                    normalization_state=self.state.normalization_state,
                ),
            ),
        )
        self.vla = ResultView(
            self.frame_result,
            ResultViewState(
                title="Vertical Long Axis (VLA)",
                axis_labels=AxisLabelState("Anterior", "Basis", "Apex", "Inferior"),
                slice_view_state=SliceViewState(
                    sitk_img_state=self.state.img_vla_state,
                    slice_state=0, # this will be set to the image center in the init of ResultViewState
                    resolution_state=self.state.resolution_state,
                    normalization_state=self.state.normalization_state,
                ),
            ),
        )

        self.view_trans.grid(column=0, row=0, padx=20, pady=5)
        self.view_sagittal.grid(column=0, row=1, padx=20, pady=5)
        self.frame_reorie.grid(column=0, row=0, rowspan=2, padx=5, pady=5)

        self.hla.grid(column=0, row=0, padx=(20, 5), pady=5)
        self.sa.grid(column=0, row=1, padx=(20, 5), pady=5)
        self.vla.grid(column=1, row=1, padx=(5, 20), pady=5)
        self.frame_result.grid(column=1, row=0, rowspan=2, padx=5, pady=5)

        self.normalization_scale.grid(column=2, row=0, rowspan=2)

        self.bind("<Key-q>", lambda event: exit(0))
        ttk.Style().theme_use("clam")
