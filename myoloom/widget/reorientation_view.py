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
from widget_state.util import compute

from .slice_view import SliceView, SliceViewState, SITKData


def cart2pol(pt: PointState) -> PointState[FloatState]:
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
    x, y = pt.values()
    distance = np.sqrt(x**2 + y**2)
    angle = np.arctan2(y, x)
    return PointState(distance, angle)


def pol2cart(pt: PointState) -> PointState[IntState]:
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
    distance, angle = pt.values()
    x = distance * np.cos(angle)
    y = distance * np.sin(angle)
    return PointState(round(x), round(y))


class ReorientationViewState(HigherOrderState):

    def __init__(
        self,
        slice_view_state: SliceViewState,
        title: StringState,
        center: PointState,
        x: Optional[FloatState] = None,
        y: Optional[FloatState] = None,
        angle: Optional[FloatState] = None,
        distance: Optional[FloatState] = None,
        start_angle: Optional[FloatState] = None,
        rectangle_size: Optional[IntState] = None,
        style_center: Optional[RectangleStyle] = None,
        style_angle: Optional[RectangleStyle] = None,
        style_line: Optional[LineStyle] = None,
    ):
        """
        Parameters
        ----------
        slice_view_state: SliceViewState
        title: StringState
        center: PointState
            center in image coordinates
        """
        super().__init__()

        self.slice_view_state = slice_view_state
        self.title = title

        sitk_img = slice_view_state.sitk_img.value
        self.center = center
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
        print(f" - Distance {self.distance}, {sitk_img.GetHeight()=}")

    @computed
    def pos_rect_angle_1(
        self,
        distance: FloatState,
        angle: FloatState,
        start_angle: FloatState,
        center: PointState,
    ) -> PointState:
        return center + pol2cart(
            PointState(distance.value, angle.value + start_angle.value)
        )

    @computed
    def pos_rect_angle_2(
        self,
        distance: FloatState,
        angle: FloatState,
        start_angle: FloatState,
        center: PointState,
    ) -> PointState:
        return center - pol2cart(
            PointState(distance.value, angle.value + start_angle.value)
        )


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
        self.title.grid(column=0, row=0)

        self.slice_view = SliceView(self, state.slice_view_state)
        self.slice_view.grid(column=0, row=1, sticky="nswe")

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=9)

        self.image = self.slice_view.image
        self.canvas = self.slice_view.canvas

        pos_rect_angle_1 = compute(
            [state.pos_rect_angle_1, self.canvas._state],
            lambda: PointState(*self.image.to_canvas(*state.pos_rect_angle_1.values())),
        )
        pos_rect_angle_2 = compute(
            [state.pos_rect_angle_2, self.canvas._state],
            lambda: PointState(*self.image.to_canvas(*state.pos_rect_angle_2.values())),
        )

        self.line = Line(
            self.canvas,
            LineState(
                LineData(pos_rect_angle_1, pos_rect_angle_2),
                style=state.style_line,
            ),
        )
        self.rect_angle_1 = Rectangle(
            self.canvas,
            RectangleState(
                RectangleData(
                    pos_rect_angle_1,
                    state.rectangle_size,
                ),
                style=state.style_angle,
            ),
        )
        self.rect_angle_2 = Rectangle(
            self.canvas,
            RectangleState(
                RectangleData(
                    pos_rect_angle_2,
                    state.rectangle_size,
                ),
                style=state.style_angle,
            ),
        )

        self.rect_center = Rectangle(
            self.canvas,
            RectangleState(
                RectangleData(
                    center=compute(
                        [state.center, self.canvas._state],
                        lambda: PointState(
                            *self.image.to_canvas(*state.center.values())
                        ),
                    ),
                    size=state.rectangle_size,
                ),
                style=state.style_center,
            ),
        )

        # def test_focus(ev, rect):
        #     print(f"Focus center rect {rect.id}...")
        #     self.canvas.focus_set()
        #     self.canvas.focus(rect.id)
        #     # self.canvas.focus_force()
        #
        # def test_left(ev, rect):
        #     print(f"Left key on center_rect {rect.x}")
        #     # self.canvas.focus(rect.id)
        #
        # def move_center(x: int = 0, y: int = 0):
        #     state.center.set(x=state.center.x.value + x)
        #     state.center.set(y=state.center.y.value + y)
        #     # I don't know why but without this the canvas losses focus
        #     self.canvas.focus_set()
        #
        # self.canvas.bind("<Left>", lambda _: move_center(x=-1))
        # self.canvas.bind("<Right>", lambda _: move_center(x=+1))
        # self.canvas.bind("<Up>", lambda _: move_center(y=-1))
        # self.canvas.bind("<Down>", lambda _: move_center(y=+1))
        # self.canvas.bind("<Button-1>", lambda _: self.canvas.focus_set())
        # self.rect_center.tag_bind("Button-1", lambda *_: self.canvas.focus_set())

        # self.canvas.config(highlightthickness=3, highlightcolor="yellow")
        self.rect_center.tag_bind(
            "<B1-Motion>",
            lambda ev, rect: state.center.set(
                *self.image.to_image_continuous(ev.x, ev.y)
            ),
        )
        self.rect_angle_1.tag_bind("<B1-Motion>", self.on_rect_angle_motion)
        self.rect_angle_2.tag_bind("<B1-Motion>", self.on_rect_angle_motion)

    def on_rect_angle_motion(self, event, rectangle):
        pos_angle = PointState(*self.image.to_image_continuous(event.x, event.y))

        # update angle and distance
        _distance, _angle = cart2pol(pos_angle - self._state.center).values()
        _angle = (_angle - self._state.start_angle.value) % (2.0 * np.pi)
        if rectangle == self.rect_angle_2:
            _angle = (_angle + np.deg2rad(180.0)) % (2.0 * np.pi)

        self._state.distance.set(_distance)
        self._state.angle.set(_angle)
