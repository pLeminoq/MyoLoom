import tkinter as tk
from tkinter import ttk

import cv2 as cv
import numpy as np
from numpy.typing import NDArray
import SimpleITK as sitk
from reacTk.state import PointState
from reacTk.widget.chechbox import (
    Checkbox,
    CheckBoxData,
    CheckBoxProperties,
    CheckBoxState,
)
from reacTk.widget.canvas.line import Line, LineData, LineStyle, LineState
from reacTk.widget.canvas.image import Image
from reacTk.widget.canvas.text import Text, TextData, TextState, TextStyle
from widget_state import (
    HigherOrderState,
    IntState,
    compute,
    ListState,
    StringState,
    BoolState,
    computed,
)

from ..widget.slice_view import SITKData, SliceView, SliceViewState

from .test import label_locations, LABELS_SA, LABELS_HLA, LABELS_VLA


def sa_to_hla(img_sa: sitk.Image) -> sitk.Image:
    return np.transpose(img_sa, (1, 0, 2))[::-1]


def sa_to_vla(img_sa: NDArray) -> sitk.Image:
    img = img_sa[::-1]
    return np.transpose(img, (2, 1, 0))


def horizontal_line(
    image: Image,
    position: IntState,
    _from: float = None,
    _to: float = None,
) -> LineData:
    _from = 0.0 if _from is None else _from
    _to = 1.0 if _to is None else _to
    return LineData(
        start=image.point_to_canvas(
            PointState(round(_from * image.array().shape[1]), position)
        ),
        end=image.point_to_canvas(
            PointState(round(_to * image.array().shape[1]), position)
        ),
    )


def vertical_line(
    image: Image,
    position: IntState,
    _from: float = None,
    _to: float = None,
) -> LineData:
    _from = 0.0 if _from is None else _from
    _to = 1.0 if _to is None else _to
    return LineData(
        start=image.point_to_canvas(
            PointState(position, round(_from * image.array().shape[0]))
        ),
        end=image.point_to_canvas(
            PointState(position, round(_to * image.array().shape[0]))
        ),
    )


class ConfigViewState(HigherOrderState):

    def __init__(self, img_sa):
        super().__init__()

        self.img_sa = img_sa if isinstance(img_sa, SITKData) else SITKData(img_sa)
        # self.sitk_hla = sitk_hla if isinstance(sitk_hla, SITKData) else SITKData(sitk_hla)

        self.center_z = IntState(0)
        self.pos_line_lateral = IntState(0)
        self.pos_line_septal = IntState(0)
        self.weighting = BoolState(True)

        self.pos_line_lateral_vla = self.pos_line_lateral.transform(
            self_to_other=lambda s: IntState(self.img_vla.value.GetSize()[0] - s.value),
            other_to_self=lambda s: IntState(self.img_vla.value.GetSize()[0] - s.value),
        )

        self.img_sa.on_change(self.init_config, trigger=True)

    @computed
    def img_hla(self, img_sa):
        img = img_sa.value
        img = sitk.GetArrayFromImage(img)
        img = sa_to_hla(img)
        img = sitk.GetImageFromArray(img)
        return SITKData(img)

    @computed
    def img_vla(self, img_sa):
        img = img_sa.value
        img = sitk.GetArrayFromImage(img)
        img = sa_to_vla(img)
        img = sitk.GetImageFromArray(img)
        return SITKData(img)

    def init_config(self, sitk_hla: SITKData):
        # TODO: we should try to estimate these values
        self.center_z.value = sitk_hla.value.GetSize()[0] // 2
        self.pos_line_lateral.value = self.center_z.value + round(
            2.0 * self.center_z.value / 3.0
        )
        self.pos_line_septal.value = self.pos_line_lateral.value

    def sampling_params(self):
        center_z = self.center_z.value
        n_lateral = self.pos_line_lateral.value - center_z + 1
        n_septal = self.pos_line_septal.value - center_z + 1

        return {"center_z": center_z, "n_lateral": n_lateral, "n_septal": n_septal}


class ConfigView(ttk.Frame):

    def __init__(self, parent: tk.Widget, state: ConfigViewState):
        super().__init__(parent)

        self.state = state

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=5, minsize=256)
        self.rowconfigure(1, weight=5, minsize=256)
        self.rowconfigure(2, weight=5, minsize=256)
        self.rowconfigure(3, weight=1, minsize=20)

        self.slice_view = SliceView(
            self, SliceViewState(self.state.img_hla, colormap=cv.COLORMAP_INFERNO)
        )
        self.slice_view.grid(row=0, column=0, sticky="nswe", pady=5)
        label_locations(self.slice_view.image, LABELS_HLA)

        self.sa = SliceView(
            self, SliceViewState(self.state.img_sa, colormap=cv.COLORMAP_INFERNO)
        )
        self.sa.grid(row=1, column=0, sticky="nswe", pady=5)
        label_locations(self.sa.image, LABELS_SA)

        self.vla = SliceView(
            self, SliceViewState(self.state.img_vla, colormap=cv.COLORMAP_INFERNO)
        )
        self.vla.grid(row=2, column=0, sticky="nswe", pady=5)
        label_locations(self.vla.image, LABELS_VLA)

        self.chechbox = Checkbox(
            self, CheckBoxState(self.state.weighting, CheckBoxProperties("Weighting"))
        )
        self.chechbox.grid(row=3, column=0, pady=5)

        # reset displayed size to center of the image changes
        self.state.img_sa.on_change(lambda _: self.reset_sliders())

        self.overlay_items = []
        self.draw_overlay()
        self.state.img_sa.on_change(lambda _: self.draw_overlay())

    def reset_sliders(self):
        _center = self.state.img_sa.value.GetSize()[0] // 2
        self.slice_view._state.slice.set(_center)
        self.sa._state.slice.set(_center)
        self.vla._state.slice.set(_center)

    def draw_overlay(self):
        for item in self.overlay_items:
            item.delete()
        self.overlay_items.clear()

        self.line_center_z = Line(
            self.slice_view.canvas,
            LineState(
                data=horizontal_line(
                    self.slice_view.image,
                    position=self.state.center_z,
                    _from=0.2,
                    _to=0.8,
                ),
                style=LineStyle(
                    color="blue", width=2, dash=ListState([IntState(8), IntState(5)])
                ),
            ),
        )
        self.line_center_z.tag_bind("<B1-Motion>", self.on_motion_line_center)
        self.overlay_items.append(self.line_center_z)

        self.line_septal = Line(
            self.slice_view.canvas,
            LineState(
                data=horizontal_line(
                    self.slice_view.image,
                    position=self.state.pos_line_septal,
                    _from=0.25,
                    _to=0.48,
                ),
                style=LineStyle(
                    color="blue", width=2, dash=ListState([IntState(8), IntState(5)])
                ),
            ),
        )
        self.line_lateral = Line(
            self.slice_view.canvas,
            LineState(
                data=horizontal_line(
                    self.slice_view.image,
                    position=self.state.pos_line_lateral,
                    _from=0.52,
                    _to=0.75,
                ),
                style=LineStyle(
                    color="blue", width=2, dash=ListState([IntState(8), IntState(5)])
                ),
            ),
        )
        self.overlay_items.append(self.line_septal)
        self.overlay_items.append(self.line_lateral)

        # TODO: Draw a line from detected myocard on these positions to indicate angle

        self.line_septal.tag_bind("<B1-Motion>", self.on_motion_line_septal)
        self.line_lateral.tag_bind("<B1-Motion>", self.on_motion_line_lateral)

        self.line_vla = Line(
            self.vla.canvas,
            LineState(
                data=vertical_line(
                    self.vla.image,
                    self.state.pos_line_lateral_vla,
                    _from=0.25,
                    _to=0.75,
                ),
                style=LineStyle(
                    color="blue", width=2, dash=ListState([IntState(8), IntState(5)])
                ),
            ),
        )
        self.line_vla.tag_bind("<B1-Motion>", self.on_motion_line_vla)
        self.overlay_items.append(self.line_vla)

        text_offset_horizontal = 4
        self.text_pos_septal = Text(
            self.slice_view.canvas,
            TextState(
                TextData(
                    self.state.pos_line_septal.transform(
                        lambda s: StringState(s.value)
                    ),
                    position=self.line_septal._state.data.start
                    + PointState(-text_offset_horizontal, 0),
                ),
                TextStyle(color="white", anchor="e"),
            ),
        )
        self.text_pos_lateral = Text(
            self.slice_view.canvas,
            TextState(
                TextData(
                    self.state.pos_line_lateral.transform(
                        lambda s: StringState(s.value)
                    ),
                    position=self.line_lateral._state.data.end
                    + PointState(text_offset_horizontal, 0),
                ),
                TextStyle(color="white", anchor="w"),
            ),
        )
        self.overlay_items.append(self.text_pos_septal)
        self.overlay_items.append(self.text_pos_lateral)

    def on_motion_line_vla(self, event, _):
        x = self.slice_view.image.to_image(event.x, event.y)[0]
        x = max(0, x)
        self.state.pos_line_lateral_vla.set(x)

    def on_motion_line_center(self, event, _):
        y = self.slice_view.image.to_image(event.x, event.y)[1]
        y = min(self.state.pos_line_septal.value - 1, y)
        self.state.center_z.set(y)

    def on_motion_line_septal(self, event, _):
        y = self.slice_view.image.to_image(event.x, event.y)[1]
        y = max(self.state.center_z.value + 1, y)
        self.state.pos_line_septal.set(y)

        if self.state.pos_line_septal.value > self.state.pos_line_lateral.value:
            self.state.pos_line_lateral.value = self.state.pos_line_septal.value

    def on_motion_line_lateral(self, event, _):
        y = self.slice_view.image.to_image(event.x, event.y)[1]
        y = min(self.state.img_sa.value.GetSize()[2], y)
        self.state.pos_line_lateral.set(y)

        if self.state.pos_line_lateral.value < self.state.pos_line_septal.value:
            self.state.pos_line_septal.value = self.state.pos_line_lateral.value


if __name__ == "__main__":
    import tkinter as tk
    from tkinter import ttk

    root = tk.Tk()

    style = ttk.Style()
    style.theme_use("clam")

    from ..util import load_image

    img_sa = load_image("data/images/0002-recon.dcm", target_range=250)
    state = ConfigViewState(img_sa)
    view = ConfigView(root, state)
    view.grid(sticky="nswe")

    root.bind("<Key-q>", lambda *args: exit(0))
    root.mainloop()
