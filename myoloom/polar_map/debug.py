"""
How should this look?

HLA | SA - Slice | Projection of SA Slice with heart contour and max-rad position
      Polar Map

TODO: Display radial activities
"""

import os
import time
import tkinter as tk
from tkinter import filedialog
from tkinter import ttk

import cv2 as cv
import numpy as np
import pandas as pd
import scipy
import SimpleITK as sitk
from reacTk.state import PointState
from reacTk.widget.canvas.line import Line, LineData, LineStyle, LineState
from reacTk.widget.canvas.canvas import Canvas, CanvasState
from reacTk.widget.canvas.image import Image, ImageData, ImageState, ImageStyle
from reacTk.widget.chechbox import (
    Checkbox,
    CheckBoxData,
    CheckBoxState,
    CheckBoxProperties,
)
from widget_state import (
    HigherOrderState,
    compute,
    computed,
    NumberState,
    ListState,
    ObjectState,
    StringState,
)

from ..util import load_image, square_pad, get_empty_image, normalize_image
from ..widget.scale import Scale, ScaleState
from ..widget.slice_view import SITKData, SliceView, SliceViewState

from .config_view import ConfigViewState, ConfigView
from .sampling import polar_grid
from .polar_map import PolarMap, PolarMapState
from .util import weight_polar_rep


class AppState(HigherOrderState):

    def __init__(self):
        super().__init__()

        self.filename = StringState("")
        self.filename_save = StringState("")

        self.enable_weighting = CheckBoxData(True)
        self.sigma = NumberState(3.0)

        self.radii_step = NumberState(0.25)
        self.radii = ObjectState(
            np.arange(0, self.sitk_sa.value.GetSize()[0] / 2, self.radii_step.value)
        )
        self.azimuth_angles = ObjectState(np.deg2rad(np.arange(0, 360, 3)))
        self.polar_angles = ObjectState(np.deg2rad(np.arange(0, 90, (90 / 10) - 0.001)))

        self.config_view_state = ConfigViewState(self.sitk_sa)
        self.polar_map_state = PolarMapState(self.radial_activities)

        self.slice_sa = NumberState(0)
        self.sitk_sa.on_change(
            lambda _: self.slice_sa.set(self.config_view_state.center_z.value + 1),
            trigger=True,
        )


        self._validate_computed_states()

    @computed
    def sitk_sa(self, filename: StringState) -> SITKData:
        if filename.value == "":
            return SITKData(get_empty_image(size=(32, 32, 32)))

        sitk_sa = load_image(filename.value, target_range=220)
        sitk_sa = square_pad(sitk_sa)
        return SITKData(sitk_sa)

    @computed
    def sitk_hla(self, sitk_sa: SITKData) -> SITKData:
        sitk_img = sitk_sa.value

        hla = sitk.GetArrayFromImage(sitk_img)
        hla = np.transpose(hla, (1, 0, 2))[::-1]
        sitk_hla = sitk.GetImageFromArray(hla)
        return SITKData(sitk_hla)

        # retrieve image center for rotation (around the center)
        center_image_idx = list(map(lambda x: x / 2, sitk_img.GetSize()))
        center_image_phys = sitk_img.TransformContinuousIndexToPhysicalPoint(
            center_image_idx
        )

        euler_trans = sitk.Euler3DTransform(center_image_phys, np.deg2rad(90), 0.0, 0.0)
        return SITKData(
            sitk.Resample(
                sitk_img,
                euler_trans,
                sitk.sitkLinear,
                0.0,
            )
        )

    @computed
    def sa_img(self, sitk_sa: SITKData, slice_sa: NumberState) -> ImageData:
        sa_img = sitk.GetArrayFromImage(sitk_sa.value)
        sa_img = normalize_image(sa_img)
        sa_img = sa_img[slice_sa.value]
        sa_img = cv.applyColorMap(sa_img, cv.COLORMAP_INFERNO)
        sa_img = cv.cvtColor(sa_img, cv.COLOR_BGR2RGB)
        return ImageData(sa_img)

    @computed
    def polar_rep(
        self,
        sitk_sa: SITKData,
        radii: ObjectState,
        azimuth_angles: ObjectState,
        polar_angles: ObjectState,
        config_view_state: ConfigViewState,
        enable_weighting: CheckBoxData,
        sigma: NumberState,
    ) -> ObjectState:
        img = sitk.GetArrayFromImage(self.sitk_sa.value)

        # since = time.time()
        grid = polar_grid(
            img,
            radii.value,
            azimuth_angles.value,
            polar_angles.value,
            **config_view_state.sampling_params(),
        )
        polar_rep = scipy.ndimage.map_coordinates(img, grid, order=3)

        if enable_weighting.value:
            pixel_size_mm = self.sitk_sa.value.GetSpacing()[0] * self.radii_step.value
            polar_rep = weight_polar_rep(polar_rep, pixel_size_mm=pixel_size_mm, sigma=sigma.value)

        # print(
        #     f"Sampling with grid {grid[0].shape} took {1000*(time.time() - since):.3f}ms"
        # )
        return ObjectState(polar_rep)

    @computed
    def radial_activities(
        self,
        polar_rep: ObjectState,
        polar_angles: ObjectState,
    ) -> ImageData:
        # a polar map is computed from the maximal value along the radius for each azimuth angle
        radial_activities = np.max(polar_rep.value, axis=1)

        # The polar rep can be/is likely imbalanced along the z axis.
        # This is because it contains n=#polar_angles slices for the apex and m slices for the cylindrical region.
        # According to the polar map model m should be 3*n.
        # This is ensured by the following code.
        activities_apex = radial_activities[: len(polar_angles.value)]
        activities_other = radial_activities[len(polar_angles.value) :]
        activities_other = cv.resize(
            activities_other, (activities_other.shape[1], activities_apex.shape[0] * 3)
        )
        radial_activities = np.concat([activities_apex, activities_other], axis=0)

        # normalize the activities
        if radial_activities.max() > 0.0:
            radial_activities = radial_activities / radial_activities.max()

        return ImageData(radial_activities)

    @computed
    def rad_act_image(self, radial_activities: ImageData) -> ImageData:
        img = radial_activities.value

        img = (255 * img).astype(np.uint8)
        img = cv.applyColorMap(img, cv.COLORMAP_INFERNO)
        img = cv.cvtColor(img, cv.COLOR_BGR2RGB)

        scale = 512 / img.shape[1]

        img = cv.resize(img, None, fx=scale, fy=scale)
        return ImageData(img)

    @computed
    def polar_slice(
        self,
        polar_rep: ObjectState,
        slice_sa: NumberState,
        polar_angles: ObjectState,
    ) -> ImageData:
        img = polar_rep.value

        if img.max() > 0.0:
            img = img / img.max()
            img = np.clip(img, a_min=0.0, a_max=1.0)
        img = img[slice_sa.value - (len(polar_angles.value) + 1)]

        max_pos = np.argmax(img, axis=0)

        img = (img * 255).astype(np.uint8)
        img = cv.applyColorMap(img, cv.COLORMAP_INFERNO)

        for i in range(img.shape[1]):
            img[max_pos[i], i] = (255, 255, 255)

        img = cv.cvtColor(img, cv.COLOR_BGR2RGB)
        return ImageData(img)


class MenuFile(tk.Menu):
    """
    The File menu containing options to open images and to
    save the current state.
    """

    def __init__(self, menu_bar, app_state):
        super().__init__(menu_bar)

        self.menu_bar = menu_bar
        self.app_state = app_state

        menu_bar.add_cascade(menu=self, label="File")

        # add commands
        self.add_command(label="Open", command=self.open)
        self.add_command(label="Save", command=self.save)
        self.add_command(label="Save As", command=self.save_as)

    def open(self):
        self.app_state.filename.set(filedialog.askopenfilename())

    def save(self):
        filename_save = self.app_state.filename_save.value

        if filename_save == "":
            return

        filename = self.app_state.filename.value
        basename = filename.split("/")[-1]
        path = filename[: -len(basename)]
        _id = basename.split("-")[0]
        filename = f"{path}{_id}-polar_map-myoloom.png"

        table_new = pd.DataFrame(
            {
                "filename": filename,
                "segment_scores": [
                    ";".join(
                        [
                            str(s.value)
                            for s in self.app_state.polar_map_state.segment_scores
                        ]
                    )
                ],
            }
        )

        if os.path.isfile(filename_save):
            table = pd.read_csv(filename_save)
            index = table[table["filename"] == self.app_state.filename.value].index
            table = table.drop(index=index)
            # concatenate current state
            table = pd.concat((table, table_new), ignore_index=False)
        else:
            table = table_new
        table.to_csv(filename_save, index=False)

    def save_as(self):
        self.app_state.filename_save.set(filedialog.asksaveasfilename())
        self.save()


class MenuBar(tk.Menu):
    """
    Menu bar of the app.
    """

    def __init__(self, root, app_state):
        super().__init__(root)

        root.option_add("*tearOff", False)
        root["menu"] = self

        self.menu_file = MenuFile(self, app_state)


class App(ttk.Frame):

    def __init__(self, parent: tk.Widget, state: AppState) -> None:
        super().__init__(parent)

        self.state = state

        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        self.columnconfigure(2, weight=1)

        self.weighting_checkbox = Checkbox(
            self,
            CheckBoxState(
                self.state.enable_weighting, CheckBoxProperties("Weighting:")
            ),
        )
        self.weighting_checkbox.grid(row=2, column=1)
        self.scale = Scale(self, ScaleState(self.state.sigma, min_value=1.0, max_value=20.0, length=256, orientation="horizontal"))
        self.scale.grid(row=2, column=0)

        self.config_view = ConfigView(self, self.state.config_view_state)
        self.config_view.grid(row=0, column=0, sticky="nswe")

        # self.slice_sa_line = self.config_view.draw_horizontal_line(
        #     state.slice_sa, color="white"
        # )
        # self.slice_sa_line.tag_bind("<B1-Motion>", self.update_slice)

        self.canvas = Canvas(self, CanvasState())
        self.canvas.grid(row=0, column=1, sticky="nswe")
        self.sa_image = Image(self.canvas, ImageState(state.sa_img))

        self.canvas_2 = Canvas(self, CanvasState())
        self.canvas_2.grid(row=0, column=2, sticky="nswe")
        self.polar_image = Image(self.canvas_2, ImageState(state.polar_slice))

        self.polar_map = PolarMap(self, state.polar_map_state)
        self.polar_map.grid(column=1, row=1, columnspan=2, sticky="nswe")

        self.canvas_img = Canvas(self, CanvasState())
        self.rad_act_image = Image(
            self.canvas_img, ImageState(self.state.rad_act_image)
        )
        self.canvas_img.grid(column=0, row=1, sticky="nswe")

    def update_slice(self, event, _):
        y = self.config_view.slice_view.image.to_image(event.x, event.y)[1]
        y = max(
            self.state.config_view_state.center_z.value
            - len(self.state.polar_angles.value),
            y,
        )
        y = min(self.state.config_view_state.pos_line_lateral.value, y)
        self.state.slice_sa.set(y)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--image", type=str)
    args = parser.parse_args()

    root = tk.Tk()
    root.title("Polar Map - Debugging")
    root.rowconfigure(0, weight=1, minsize=900)
    root.columnconfigure(0, weight=1, minsize=900)

    style = ttk.Style()
    style.theme_use("clam")

    app_state = AppState()
    if args.image:
        app_state.filename.value = args.image
    else:
        root.after(100, lambda: app_state.filename.set(filedialog.askopenfilename()))

    app = App(root, app_state)
    app.grid(sticky="nswe")

    menu_bar = MenuBar(root, app_state)

    root.bind("<Key-q>", lambda event: exit(0))
    root.mainloop()
