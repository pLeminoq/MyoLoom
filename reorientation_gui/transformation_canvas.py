from typing import Tuple

import cv2 as cv
import numpy as np
from PIL import Image, ImageTk
import tkinter as tk

from reorientation_gui.state.lib import State


class Point(State):

    def __init__(self, x: int, y: int):
        super().__init__()

        self.x = x
        self.y = y

    def __iter__(self):
        return iter((self.x, self.y))

    def __getitem__(self, i):
        return (self.x, self.y)[i]

    def update(self, x: int, y: int, notify=True):
        print(f"Update point to {(x, y)}")
        self.x = x
        self.y = y
        
        if notify:
            self.notify_change()

    def rect(self, size: int):
        """
        Get the top-left und bottom-right points of a rectangle around this point.

        Parameters
        ----------
        size: int
            the size of the rectangle

        Returns
        -------
        list of int
            list of format [left, top, right, bottom]
        """
        size_h = size // 2
        return [
            self.x - size_h,
            self.y - size_h,
            self.x + size_h,
            self.y + size_h,
        ]


class ReorientationCanvasState(State):

    def __init__(self, p_center: Tuple[int, int], p_angle: Tuple[int, int]):
        super().__init__()

        self.p_center = Point(*p_center)
        self.p_angle = Point(*p_angle)
        self.angle = 0.0
        self.compute_angle()

        self.p_center.on_change(lambda *args: self.compute_angle())
        self.p_center.on_change(lambda *args: self.notify_change())

        self.p_angle.on_change(lambda *args: self.compute_angle())
        self.p_angle.on_change(lambda *args: self.notify_change())

    def compute_angle(self) -> float:
        """
        Compute the angle between a vector from p_center to p_angle and the
        horizontal axes.

        Returns
        -------
        angle: float
            the angle in radians
        """
        x_c, y_c = self.p_center
        x_a, y_a = self.p_angle

        # create normalized vector from center point to angle defining point
        vec_1 = np.array([x_a - x_c, y_a - y_c])
        vec_1 = vec_1 / np.linalg.norm(vec_1)
        # create normalized horizontal vector
        vec_2 = np.array([1, 0])

        # compute angle
        angle = np.arccos(np.dot(vec_1, vec_2))
        # make sure that rotation covers 360° (p_angle above p_center is a positive rotation, else negative)
        if y_a > y_c:
            angle = -angle
        self.angle = angle


class ReorientationCanvas(tk.Canvas):
    """ """

    def __init__(
        self,
        parent: tk.Frame,
        img: ImageTk,
        width: int = 512,
        height: int = 512,
        p_size: int = 10,
        p_center: Tuple[int, int] = (256, 256),
        p_center_color: str = "green",
        p_angle: Tuple[int, int] = (286, 226),
        p_angle_color: str = "blue",
        line_color: str = "black",
    ):
        super().__init__(parent, width=width, height=height)
        self.img = img
        self.width = width
        self.height = height
        self.p_size = p_size
        self.p_size_h = self.p_size // 2
        self.p_center_color = p_center_color
        self.p_angle_color = p_angle_color
        self.line_color = line_color

        self.state = ReorientationCanvasState(
            p_center,
            p_angle,
        )

        self._draw()

        self.state.p_center.on_change(lambda *args: self.redraw_p_center())
        self.state.p_angle.on_change(lambda *args: self.redraw_p_angle())

    def _draw(self):
        """
        Initial drawing of the HeartRotationCanvas.
        """
        # draw the background image
        self.img_id = self.create_image(
            self.width // 2, self.height // 2, image=self.img
        )
        # draw a line from p_center to p_angle
        # this is done before the points so that the line is behind them
        self.line_id = self.create_line(
            *self.state.p_center, *self.state.p_angle, fill=self.line_color
        )
        # draw the points
        self.p_center_id = self.create_rectangle(
            *self.state.p_center.rect(self.p_size),
            fill=self.p_center_color,
        )
        self.p_angle_id = self.create_rectangle(
            *self.state.p_angle.rect(self.p_size),
            fill=self.p_angle_color,
        )
        self.tag_bind(
            self.p_center_id,
            "<B1-Motion>",
            # lambda *args: print("Motion on p_center?"),
            lambda *args: self.state.p_center.update(*self.get_pointer_xy()),
        )
        self.tag_bind(
            self.p_angle_id,
            "<B1-Motion>",
            lambda *args: self.state.p_angle.update(*self.get_pointer_xy()),
        )

    def get_pointer_xy(self):
        """
        Get the position of the mouse pointer on the canvas.

        Returns
        -------
        x, y: int, int
        """
        x, y = self.winfo_pointerxy()
        x -= self.winfo_rootx()
        y -= self.winfo_rooty()
        return x, y

    def redraw_p_center(self, *args):
        # move point
        self.coords(
            self.p_center_id,
            *self.state.p_center.rect(self.p_size),
        )
        # move start-point of line
        self.coords(self.line_id, *self.state.p_center, *self.coords(self.line_id)[2:4])

    def redraw_p_angle(self):
        # move point
        self.coords(
            self.p_angle_id,
            *self.state.p_angle.rect(self.p_size),
        )
        # move start-point of line
        self.coords(self.line_id, *self.coords(self.line_id)[0:2], *self.state.p_angle)

    def update_img(self, img: ImageTk):
        self.img = img
        self.itemconfig(self.img_id, image=self.img)
