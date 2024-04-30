from typing import Optional, Tuple

import cv2 as cv
import numpy as np
from PIL import Image, ImageTk
import tkinter as tk

from reorientation_gui.state import Point, State, FloatState
from reorientation_gui.widgets.canvas import Line, LineState, Rectangle, RectangleState
from reorientation_gui.widgets.slice_view import SliceView, SliceViewState


class ReorientationViewState(State):

    def __init__(
        self,
        slice_view: SliceViewState,
        rect_center: RectangleState,
        angle: FloatState,
        distance: float,
        rect_angle_color: str,
        line_color: str,
        title: str,
        verticle: bool = True,
    ):
        super().__init__()

        self.slice_view = slice_view
        self.rect_center = rect_center
        self.angle = angle
        self.title = title
        self.verticle = verticle

        self.rect_angle = RectangleState(
            center=Point(
                x=(
                    rect_center.center.x.value + distance * np.sin(angle.value)
                    if verticle
                    else rect_center.center.x.value - distance * np.cos(angle.value)
                ),
                y=(
                    rect_center.center.y.value - distance * np.cos(angle.value)
                    if verticle
                    else rect_center.center.y.value + distance * np.sin(angle.value)
                ),
            ),
            size=rect_center.size,
            color=rect_angle_color,
        )
        self.line = LineState(
            start=rect_center.center, end=self.rect_angle.center, color=line_color
        )

        self.rect_center.on_change(lambda _: self.update_angle())
        self.rect_center.on_change(lambda _: self.notify_change())

        self.rect_angle.on_change(lambda _: self.update_angle())
        self.rect_angle.on_change(lambda _: self.notify_change())

        self._rect_center_bck = (self.rect_center.center.x.value, self.rect_center.center.y.value)
        self._rect_angle = (self.rect_angle.center.x.value, self.rect_angle.center.y.value)
        self.slice_view.sitk_img_state.on_change(self.reset_points)


    def reset_points(self, *args):
        self.rect_center.center.x.value = self._rect_center_bck[0]
        self.rect_center.center.y.value = self._rect_center_bck[1]

        self.rect_angle.center.x.value = self._rect_angle[0]
        self.rect_angle.center.y.value = self._rect_angle[1]

    def update_angle(self):
        """
        Update the angle like clockwise.
        """
        x_c, y_c = self.rect_center.center
        x_a, y_a = self.rect_angle.center

        if x_a >= x_c and y_a < y_c:
            dist_x = x_a - x_c
            dist_y = y_c - y_a
            angle = np.arctan(dist_x / dist_y)
        elif x_a > x_c and y_a >= y_c:
            dist_x = x_a - x_c
            dist_y = y_a - y_c
            angle = np.deg2rad(90) + np.arctan(dist_y / dist_x)
        elif x_a <= x_c and y_a > y_c:
            dist_x = x_c - x_a
            dist_y = y_a - y_c
            angle = np.deg2rad(180) + np.arctan(dist_x / dist_y)
        elif x_a < x_c and y_a <= y_c:
            dist_x = x_c - x_a
            dist_y = y_c - y_a
            angle = np.deg2rad(270) + np.arctan(dist_y / dist_x)
        else:
            # error case: angle point is right on top of the center point
            angle = 0.0

        if not self.verticle:
            angle = (angle - 270) % 360

        self.angle.value = angle


class ReorientationView(tk.Frame):

    def __init__(
        self,
        parent: tk.Frame,
        state: ReorientationViewState,
    ):
        super().__init__(parent)

        self.state = state

        self.title = tk.Label(self, text=state.title)

        self.slice_view = SliceView(self, state.slice_view)
        self.canvas = self.slice_view.canvas
        self.line = Line(self.canvas, state.line)
        self.rect_center = Rectangle(self.canvas, state.rect_center)
        self.rect_angle = Rectangle(self.canvas, state.rect_angle)

        self.canvas.tag_bind(
            self.rect_center.id,
            "<B1-Motion>",
            lambda *args: self.rect_center.state.center.update(*self.get_pointer_xy()),
        )
        self.canvas.tag_bind(
            self.rect_angle.id,
            "<B1-Motion>",
            lambda *args: self.rect_angle.state.center.update(*self.get_pointer_xy()),
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
        x = max(0, min(x, self.state.slice_view.size[0]))
        y = max(0, min(y, self.state.slice_view.size[1]))

        return x, y
