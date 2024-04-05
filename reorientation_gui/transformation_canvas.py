from typing import Tuple

import cv2 as cv
import numpy as np
from PIL import Image, ImageTk
import tkinter as tk

class ReorientationCanvas(tk.Canvas):
    """ """

    def __init__(
        self,
        parent: tk.Frame,
        img: ImageTk,
        width:int=512,
        height:int=512,
        p_size:int=10,
        p_center:Tuple[int, int]=(256, 256),
        p_center_color:str="green",
        p_angle:Tuple[int, int]=(286, 226),
        p_angle_color:str="blue",
        line_color:str="black",
    ):
        super().__init__(parent, width=width, height=height)
        self.img = img
        self.width = width
        self.height = height
        self.p_size = p_size
        self.p_size_h = self.p_size // 2
        self.p_center = p_center
        self.p_center_color = p_center_color
        self.p_angle = p_angle
        self.p_angle_color = p_angle_color
        self.line_color = line_color
        self.callbacks = []

        self.angle = self._compute_angle()
        self._draw()


    def _draw(self):
        """
        Initial drawing of the HeartRotationCanvas.
        """
        # draw the background image
        self.img_id = self.create_image(self.width // 2, self.height // 2, image=self.img)
        # draw a line from p_center to p_angle
        # this is done before the points so that the line is behind them
        self.line_id = self.create_line(*self.p_center, *self.p_angle, fill=self.line_color)
        # draw the points
        self.p_center_id = self.create_rectangle(
            self.p_center[0] - self.p_size_h,
            self.p_center[1] - self.p_size_h,
            self.p_center[0] + self.p_size_h,
            self.p_center[1] + self.p_size_h,
            fill=self.p_center_color,
        )
        self.p_angle_id = self.create_rectangle(
            self.p_angle[0] - self.p_size_h,
            self.p_angle[1] - self.p_size_h,
            self.p_angle[0] + self.p_size_h,
            self.p_angle[1] + self.p_size_h,
            fill=self.p_angle_color,
        )
        self.tag_bind(self.p_center_id, "<B1-Motion>", self.move_p_center)
        self.tag_bind(self.p_angle_id, "<B1-Motion>", self.move_p_angle)

    def _compute_angle(self) -> float:
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
        return angle

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

    def move_p_center(self, event):
        # store mouse position as new center position
        self.p_center = self.get_pointer_xy()
        # move center point
        self.coords(
            self.p_center_id,
            self.p_center[0] - self.p_size_h,
            self.p_center[1] - self.p_size_h,
            self.p_center[0] + self.p_size_h,
            self.p_center[1] + self.p_size_h,
        )
        # move start-point of line
        self.coords(self.line_id, *self.p_center, *self.coords(self.line_id)[2:4])
        # notify_angle angle change
        self.notify_transformation()

    def move_p_angle(self, event):
        # store mouse position as new angle position
        self.p_angle = self.get_pointer_xy()
        # move center point
        self.coords(
            self.p_center_id,
            self.p_center[0] - self.p_size_h,
            self.p_center[1] - self.p_size_h,
            self.p_center[0] + self.p_size_h,
            self.p_center[1] + self.p_size_h,
        )
        # move start-point of line
        self.coords(self.line_id, *self.p_center, *self.coords(self.line_id)[2:4])
        # notify_angle angle change
        self.notify_transformation()
        x, y = self.get_pointer_xy()
        self.coords(
            self.p_angle_id,
            x - self.p_size_h,
            y - self.p_size_h,
            x + self.p_size_h,
            y + self.p_size_h,
        )
        _x, _y, _, _ = self.coords(self.line_id)
        self.coords(self.line_id, _x, _y, x, y)
        self.notify_transformation()

    def notify_transformation(self):
        self.angle = self._compute_angle()
        for cb in self.callbacks:
            cb(self.angle, self.p_center)

    def on_change(self, callback):
        self.callbacks.append(callback)

    def update_img(self, img: ImageTk):
        self.img = img
        self.itemconfig(self.img_id, image=self.img)

