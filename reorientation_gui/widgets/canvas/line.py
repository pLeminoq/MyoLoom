from typing import Optional

import tkinter as tk

from reorientation_gui.state import Point, State


class LineState(State):

    def __init__(self, start: Point, end: Point, color: str):
        super().__init__()

        self.start = start
        self.end = end
        self.color = color

        self.start.on_change(lambda _: self.notify_change(ignore_change=True))
        self.end.on_change(lambda _: self.notify_change(ignore_change=True))

    def update(self, color: Optional[str]):
        color = color if color is not None else self.color
        self.notify_change()


class Line:

    def __init__(self, canvas: tk.Canvas, state: LineState):
        self.canvas = canvas
        self.state = state

        self.id = self.canvas.create_line(
            *self.state.start,
            *self.state.end,
            fill=self.state.color,
        )

        self.state.on_change(self.redraw)

    def redraw(self, state):
        self.canvas.coords(self.id, *state.start, *state.end)
        self.canvas.itemconfig(self.id, fill=state.color)
