"""
Widget to configure the reorientation through user input. 
"""

from typing import Optional, Tuple

import cv2 as cv
import numpy as np
from PIL import Image, ImageTk
import tkinter as tk
from tkinter import ttk

from reacTk.state import PointState
from reacTk.widget.label import Label, LabelState
from reacTk.widget.canvas.line import Line, LineData, LineState, LineStyle
from reacTk.widget.canvas.rectangle import (
    Rectangle,
    RectangleData,
    RectangleState,
    RectangleStyle,
)
from widget_state import (
    HigherOrderState,
    FloatState,
    BoolState,
    StringState,
    IntState,
    computed,
)

from .slice_view import SliceView, SliceViewState, SITKData


def cart2pol(x: int, y: int) -> Tuple[float, float]:
    """
    Convert Cartesian to polar coordinates.

    Parameters
    ----------
    x: int
    y: int

    Returns
    -------
    float, float
        distance and angle in radians
    """
    distance = np.sqrt(x**2 + y**2)
    angle = np.arctan2(y, x)
    return distance, angle


def pol2cart(distance: float, angle: float) -> Tuple[int, int]:
    """
    Convert polar to Cartesian coordinates.

    Parameters
    ----------
    distance: float
    angle: float

    Returns
    -------
    int, int
        x and y coordinates
    """
    x = distance * np.cos(angle)
    y = distance * np.sin(angle)
    return round(x), round(y)


class ReorientationViewState(HigherOrderState):

    def __init__(
        self,
        slice_view_state: SliceViewState,
        title: StringState,
        center: Optional[PointState] = None,
        angle: Optional[FloatState] = None,
        distance: Optional[FloatState] = None,
        start_angle: Optional[FloatState] = None,
        rectangle_size: Optional[IntState] = None,
        style_center: Optional[RectangleStyle] = None,
        style_angle: Optional[RectangleStyle] = None,
        style_line: Optional[LineStyle] = None,
    ):
        super().__init__()

        self.slice_view_state = slice_view_state
        self.title = title

        sitk_img = slice_view_state.sitk_img.value
        self.center = (
            center
            if center is not None
            else PointState(sitk_img.GetSize()[0] // 2, sitk_img.GetSize()[1] // 2)
        )
        self.angle = angle if angle is not None else FloatState(0.0)
        self.distance = (
            distance
            if distance is not None
            else FloatState(sitk_img.GetSize()[0] / 5.0)
        )
        self.start_angle = start_angle if start_angle is not None else FloatState(0.0)

        self.rectangle_size = (
            rectangle_size if rectangle_size is not None else IntState(8)
        )
        self.style_center = (
            style_center if style_center is not None else RectangleStyle(color="green")
        )
        self.style_angle = (
            style_angle if style_angle is not None else RectangleStyle(color="blue")
        )
        self.style_line = (
            style_line if style_line is not None else LineStyle(color="white")
        )

    @computed
    def pos_rect_angle_1(
        self,
        distance: FloatState,
        angle: FloatState,
        start_angle: FloatState,
        center: PointState,
    ) -> PointState:
        _x, _y = pol2cart(distance.value, angle.value + start_angle.value)
        return PointState(center.x.value + _x, center.y.value + _y)

    @computed
    def pos_rect_angle_2(
        self,
        distance: FloatState,
        angle: FloatState,
        start_angle: FloatState,
        center: PointState,
    ) -> PointState:
        _x, _y = pol2cart(distance.value, angle.value + start_angle.value)
        return PointState(center.x.value - _x, center.y.value - _y)


class ReorientationView(ttk.Frame):

    def __init__(
        self,
        parent: tk.Widget,
        state: ReorientationViewState,
    ):
        """
        Widget used to configure reorientation parameters.

        It allows the user to configure the center for image translation,
        as well as the rotation around a single axis.
        """
        super().__init__(parent)

        self._state = state

        self.title = Label(self, state.title)
        self.title.grid(row=0, column=0)

        self.slice_view = SliceView(self, state.slice_view_state)
        self.slice_view.grid(row=1, column=0, sticky="nswe")

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=9)

        self.image = self.slice_view.image
        self.canvas = self.slice_view.canvas

        self.line = Line(
            self.canvas,
            LineState(
                LineData(
                    self.to_canvas_coordinates(state.pos_rect_angle_1),
                    self.to_canvas_coordinates(state.pos_rect_angle_2),
                ),
                style=state.style_line,
            ),
        )
        self.rect_center = Rectangle(
            self.canvas,
            RectangleState(
                RectangleData(
                    self.to_canvas_coordinates(state.center), state.rectangle_size
                ),
                style=state.style_center,
            ),
        )
        self.rect_angle_1 = Rectangle(
            self.canvas,
            RectangleState(
                RectangleData(
                    self.to_canvas_coordinates(state.pos_rect_angle_1),
                    state.rectangle_size,
                ),
                style=state.style_angle,
            ),
        )
        self.rect_angle_2 = Rectangle(
            self.canvas,
            RectangleState(
                RectangleData(
                    self.to_canvas_coordinates(state.pos_rect_angle_2),
                    state.rectangle_size,
                ),
                style=state.style_angle,
            ),
        )

        self.rect_center.tag_bind(
            "<B1-Motion>",
            lambda ev, rect: state.center.set(*self.image.to_image(ev.x, ev.y)),
        )
        self.rect_angle_1.tag_bind("<B1-Motion>", self.on_rect_angle_motion)
        self.rect_angle_2.tag_bind("<B1-Motion>", self.on_rect_angle_motion)


    def to_canvas_coordinates(self, point: PointState) -> PointState:
        res = PointState(0, 0)
        res.depends_on(
            [point, self.canvas._state],
            lambda: PointState(*self.image.to_canvas(*point.values())),
        )
        return res

    def on_rect_angle_motion(self, event, rectangle):
        x_c, y_c = self._state.center.values()
        x_a, y_a = self.image.to_image(event.x, event.y)

        # update angle and distance
        _distance, _angle = cart2pol(x_a - x_c, y_a - y_c)
        _angle = (_angle - self._state.start_angle.value) % (2.0 * np.pi)
        if rectangle == self.rect_angle_2:
            _angle = (_angle + np.deg2rad(180.0)) % (2.0 * np.pi)

        self._state.distance.set(_distance)
        self._state.angle.set(_angle)
