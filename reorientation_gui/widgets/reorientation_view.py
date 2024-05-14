from typing import Optional, Tuple

import cv2 as cv
import numpy as np
from PIL import Image, ImageTk
import tkinter as tk

from reorientation_gui.state import (
    PointState,
    HigherState,
    FloatState,
    BoolState,
    StringState,
)
from reorientation_gui.widgets.canvas import Line, LineState, Rectangle, RectangleState
from reorientation_gui.widgets.slice_view import SliceView, SliceViewState


def cart2pol(x: int, y: int) -> Tuple[float, float]:
    distance = np.sqrt(x**2 + y**2)
    angle = np.arctan2(y, x)
    return distance, angle


def pol2cart(distance: float, angle: float) -> Tuple[int, int]:
    x = distance * np.cos(angle)
    y = distance * np.sin(angle)
    return round(x), round(y)


class ReorientationViewState(HigherState):

    def __init__(
        self,
        slice_view_state: SliceViewState,
        rect_center_state: RectangleState,
        angle_state: FloatState,
        distance_state: FloatState,
        title_state: StringState,
        start_angle: FloatState = 0,
    ):
        super().__init__()

        self.slice_view_state = slice_view_state
        self.rect_center_state = rect_center_state
        self.angle_state = angle_state
        self.distance_state = distance_state
        self.title_state = title_state
        self.start_angle = start_angle

        _x, _y = pol2cart(
            self.distance_state.value, self.angle_state.value + self.start_angle.value
        )
        self.rect_angle_1_state = RectangleState(
            center_state=PointState(
                x=rect_center_state.center_state.x.value + _x,
                y=rect_center_state.center_state.y.value + _y,
            ),
            size_state=rect_center_state.size_state,
            color_state="blue",
        )
        self.rect_angle_2_state = RectangleState(
            center_state=PointState(
                x=rect_center_state.center_state.x.value - _x,
                y=rect_center_state.center_state.y.value - _y,
            ),
            size_state=rect_center_state.size_state,
            color_state="blue",
        )
        self.line = LineState(
            start_state=self.rect_angle_1_state.center_state,
            end_state=self.rect_angle_2_state.center_state,
            color_state="white",
        )

        self.rect_center_state.center_state.on_change(self.on_rect_center_change)
        self.rect_angle_1_state.center_state.on_change(self.on_rect_angle_1_change)
        self.rect_angle_2_state.center_state.on_change(self.on_rect_angle_2_change)

    def on_rect_center_change(self, state):
        _x, _y = pol2cart(
            self.distance_state.value, self.angle_state.value + self.start_angle.value
        )
        self.rect_angle_1_state.center_state.set(
            state.x.value + _x,
            state.y.value + _y,
        )

    def on_rect_angle_1_change(self, state):
        x_c, y_c = self.rect_center_state.center_state.values()
        x_a, y_a = self.rect_angle_1_state.center_state.values()

        x = x_a - x_c
        y = y_a - y_c

        # update position of rect angle 1
        self.rect_angle_2_state.center_state.x.value = x_c - x
        self.rect_angle_2_state.center_state.y.value = y_c - y

        # update angle and distance
        _distance, _angle = cart2pol(x, y)
        _angle = (_angle - self.start_angle.value) % (2.0 * np.pi)

        self.distance_state.value = _distance
        self.angle_state.value = _angle

    def on_rect_angle_2_change(self, state):
        x_c, y_c = self.rect_center_state.center_state.values()
        x_a, y_a = self.rect_angle_2_state.center_state.values()

        x = x_a - x_c
        y = y_a - y_c

        # update position of rect angle 1
        self.rect_angle_1_state.center_state.x.value = x_c - x
        self.rect_angle_1_state.center_state.y.value = y_c - y


class ReorientationView(tk.Frame):

    def __init__(
        self,
        parent: tk.Frame,
        state: ReorientationViewState,
    ):
        super().__init__(parent)

        self.state = state

        self.title = tk.Label(self, text=state.title_state.value)

        self.slice_view = SliceView(self, state=state.slice_view_state)
        self.canvas = self.slice_view.canvas
        self.line = Line(self.canvas, state.line)
        self.rect_center = Rectangle(self.canvas, state.rect_center_state)
        self.rect_angle_1 = Rectangle(self.canvas, state.rect_angle_1_state)
        self.rect_angle_2 = Rectangle(self.canvas, state.rect_angle_2_state)

        self.canvas.tag_bind(
            self.rect_center.id,
            "<B1-Motion>",
            lambda *args: self.rect_center.state.center_state.set(
                *self.get_pointer_xy()
            ),
        )
        self.canvas.tag_bind(
            self.rect_angle_1.id,
            "<B1-Motion>",
            lambda *args: self.rect_angle_1.state.center_state.set(
                *self.get_pointer_xy()
            ),
        )
        self.canvas.tag_bind(
            self.rect_angle_2.id,
            "<B1-Motion>",
            lambda *args: self.rect_angle_2.state.center_state.set(
                *self.get_pointer_xy()
            ),
        )

        self.title.grid(column=0, row=0)
        self.slice_view.grid(column=0, row=1)

    def get_pointer_xy(self):
        """
        Get the position of the mouse pointer on the canvas.

        Returns
        -------
        x, y: int, int
        """
        # get mouse position in canvas coordinates
        x, y = self.slice_view.winfo_pointerxy()
        x -= self.slice_view.winfo_rootx()
        y -= self.slice_view.winfo_rooty()

        # clip to canvas dimensions
        x = max(0, min(x, self.state.slice_view_state.resolution_state.width.value))
        y = max(0, min(y, self.state.slice_view_state.resolution_state.height.value))

        return x, y
