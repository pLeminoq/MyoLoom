import tkinter as tk
from tkinter import ttk

import cv2 as cv
import numpy as np
import SimpleITK as sitk

from reacTk.state import PointState
from reacTk.util import get_active_monitor
from reacTk.widget.canvas.rectangle import RectangleStyle

from .state import *
from .widget.menu import MenuBar
from .widget.reorientation_view import ReorientationView, ReorientationViewState
from .widget.result_view import ResultView, ResultViewState, AxisLabelState
from .widget.scale import Scale, ScaleState
from .widget.slice_view import SliceViewState


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

        monitor = get_active_monitor(self.winfo_geometry())

        slice_view_resolution = (monitor.height - 350) // 2
        print(f"{slice_view_resolution=}")

        # display_resolution = (self.winfo_screenheight() - 350) // 2
        # self.state.resolution_state.set(display_resolution, display_resolution)
        # self.state.rectangle_size_state.value = round(display_resolution * 0.02)

        # _scale = display_resolution / self.state.sitk_img_state.value.GetSize()[0]
        # _to_image_scale = lambda value: round(value / _scale)
        # _to_display_scale = lambda value: round(value * _scale)

        self.menu_bar = MenuBar(self, self.state)

        self.normalization_scale = Scale(
            self,
            state=ScaleState(
                value=self.state.clip_percentage,
                min_value=0.0,
                max_value=1.0,
                length=round(1.5 * slice_view_resolution),
                orientation=tk.VERTICAL,
                formatter="{:.0%}",
            ),
        )

        self.frame_reorie = ttk.Frame(self)
        self.view_trans = ReorientationView(
            self.frame_reorie,
            ReorientationViewState(
                slice_view_state=SliceViewState(
                    sitk_img=self.state.sitk_img,
                    slice=self.state.reorientation.center.z,  # TODO: this needs to depend on the current image/ should be initialized to its center
                    clip_percentage=self.state.clip_percentage,
                    colormap=cv.COLORMAP_INFERNO,
                ),
                title="Transversal",
                center=PointState(
                    x=self.state.reorientation.center.x,
                    y=self.state.reorientation.center.y,
                ),
                angle=self.state.reorientation.angle.z,
                distance=30.0,  # TODO: depend on display resolution
                start_angle=np.deg2rad(270),
                rectangle_size=10,  # TODO
            ),
        )

        self.view_sagittal = ReorientationView(
            self.frame_reorie,
            ReorientationViewState(
                slice_view_state=SliceViewState(
                    sitk_img=self.state.sitk_img_saggital,
                    slice=self.state.reorientation.center.x,
                    clip_percentage=self.state.clip_percentage,
                    colormap=cv.COLORMAP_INFERNO,
                ),
                title="Saggital",
                center=PointState(
                    x=self.state.reorientation.center.y,
                    y=self.state.reorientation.center.z,
                ),
                angle=self.state.reorientation.angle.x,
                distance=30.0,  # TODO: depend on display resolution
                start_angle=np.deg2rad(180),
                rectangle_size=10,  # TODO
            ),
        )

        self.frame_result = ttk.Frame(self)
        self.hla = ResultView(
            self.frame_result,
            ResultViewState(
                title="Horizontal Long Axis (HLA)",
                axis_labels=AxisLabelState("Apex", "Septal", "Lateral", "Basis"),
                slice_view_state=SliceViewState(
                    sitk_img=self.state.img_reoriented,
                    slice=46,  # TODO: this will be set to the image center in the init of ResultViewState
                    clip_percentage=self.state.clip_percentage,
                    colormap=cv.COLORMAP_INFERNO,
                ),
            ),
        )
        self.sa = ResultView(
            self.frame_result,
            ResultViewState(
                title="Short Axis (SA)",
                axis_labels=AxisLabelState("Septal", "Anterior", "Inferior", "Lateral"),
                slice_view_state=SliceViewState(
                    sitk_img=self.state.img_sa,
                    slice=46,  # TODO: this will be set to the image center in the init of ResultViewState
                    clip_percentage=self.state.clip_percentage,
                    colormap=cv.COLORMAP_INFERNO,
                ),
            ),
        )
        self.vla = ResultView(
            self.frame_result,
            ResultViewState(
                title="Vertical Long Axis (VLA)",
                axis_labels=AxisLabelState("Anterior", "Basis", "Apex", "Inferior"),
                slice_view_state=SliceViewState(
                    sitk_img=self.state.img_vla,
                    slice=46,  # TODO: this will be set to the image center in the init of ResultViewState
                    clip_percentage=self.state.clip_percentage,
                    colormap=cv.COLORMAP_INFERNO,
                ),
            ),
        )

        self.view_trans.grid(column=0, row=0, padx=20, pady=5, sticky="nswe")
        self.view_sagittal.grid(column=0, row=1, padx=20, pady=5, sticky="nswe")
        self.frame_reorie.rowconfigure(0, weight=1, minsize=slice_view_resolution)
        self.frame_reorie.rowconfigure(1, weight=1, minsize=slice_view_resolution)
        self.frame_reorie.grid(
            column=0, row=0, rowspan=2, padx=5, pady=5, sticky="nswe"
        )

        self.rowconfigure(0, weight=1, minsize=slice_view_resolution)
        self.rowconfigure(1, weight=1, minsize=slice_view_resolution)
        self.columnconfigure(0, weight=5, minsize=slice_view_resolution)
        self.columnconfigure(1, weight=5, minsize=slice_view_resolution)
        self.columnconfigure(2, weight=1)

        self.hla.grid(column=0, row=0, padx=(20, 5), pady=5, sticky="nswe")
        self.sa.grid(column=0, row=1, padx=(20, 5), pady=5, sticky="nswe")
        self.vla.grid(column=1, row=1, padx=(5, 20), pady=5, sticky="nswe")
        self.frame_result.grid(column=1, row=0, rowspan=2, padx=5, pady=5, sticky="nswe")
        self.frame_result.rowconfigure(0, weight=1, minsize=slice_view_resolution)
        self.frame_result.rowconfigure(1, weight=1, minsize=slice_view_resolution)
        self.frame_result.columnconfigure(0, weight=1, minsize=slice_view_resolution)
        self.frame_result.columnconfigure(1, weight=1, minsize=slice_view_resolution)

        self.normalization_scale.grid(column=2, row=0, rowspan=2)

        self.bind("<Key-q>", lambda event: exit(0))
        ttk.Style().theme_use("clam")
