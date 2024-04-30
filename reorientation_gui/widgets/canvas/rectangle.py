from typing import Optional

import tkinter as tk

from reorientation_gui.state import Point, State


class RectangleState(State):

    def __init__(self, center: Point, size: int, color: str):
        super().__init__()

        self.center = center
        self.size = size
        self.color = color

        self.center.on_change(lambda p: self.notify_change(ignore_change=True))
        self.center.on_change(lambda p: print(f"Center has changed?"))

    def update(self, size: Optional[int], color: Optional[str]):
        size = size if size is not None else self.size
        color = color if color is not None else self.color
        self.notify_change()

    def ltbr(self):
        size_h = self.size // 2
        x, y = self.center
        return [
            x - size_h,
            y - size_h,
            x + size_h,
            y + size_h,
        ]


class Rectangle:

    def __init__(self, canvas: tk.Canvas, state: RectangleState):
        self.canvas = canvas
        self.state = state

        self.id = self.canvas.create_rectangle(
            *self.state.ltbr(),
            fill=self.state.color,
        )

        self.state.on_change(self.redraw)

    def redraw(self, state):
        self.canvas.coords(self.id, *state.ltbr())
        self.canvas.itemconfig(self.id, fill=state.color)
