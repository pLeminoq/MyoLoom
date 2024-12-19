import tkinter as tk
from tkinter import ttk

import numpy as np
from reacTk.widget.canvas.line import Line, LineData, LineState, LineStyle
from reacTk.widget.canvas.image import Image, ImageData, ImageState, ImageStyle
from reacTk.widget.canvas.text import Text, TextData, TextState, TextStyle
from reacTk.widget.canvas import Canvas, CanvasState
from reacTk.state import PointState
from widget_state import compute, ListState, IntState, FloatState, StringState

from .state import AppState
from .segment import SEGMENTS, segment_mask, segment_center


class App(ttk.Frame):

    def __init__(self, parent: tk.Widget, state: AppState):
        super().__init__()

        self.state = state

        self.canvas = Canvas(self, CanvasState())
        self.canvas.grid(row=0, column=0, sticky="nswe")

        self.canvas_2 = Canvas(self, CanvasState())
        self.canvas_2.grid(row=0, column=1, sticky="nswe")

        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        self.image = Image(
            self.canvas,
            ImageState(
                state.central_slice,
                style=ImageStyle(fit="contain", background=True),
            ),
        )
        self.rad_line = self.horizontal_line(state.pos_rad, color="blue")
        self.cyl_line = self.horizontal_line(state.pos_cylindrical, color="green")

        self.act = Image(
            self.canvas_2,
            ImageState(
                state.polar_map,
                style=ImageStyle(fit="contain", background=True),
            ),
        )

        self.segment_scores = []
        for segment in SEGMENTS:
            mask = segment_mask(state.radial_activities.value, segment)
            score = np.average(state.radial_activities.value[mask])

            position = compute(
                [self.act._state, self.canvas._state],
                lambda segment=segment: PointState(
                    *self.act.to_canvas(
                        *segment_center(
                            segment, self.act._state.data.value.shape[0] // 2
                        )
                    )
                ),
            )
            text = compute(
                [state.radial_activities],
                lambda segment=segment: StringState(
                    round(
                        100
                        * np.average(
                            state.radial_activities.value[
                                segment_mask(state.radial_activities.value, segment)
                            ]
                        )
                    )
                ),
            )
            self.segment_scores.append(
                Text(
                    self.canvas_2,
                    TextState(
                        TextData(text, position),
                        style=TextStyle(color="white", anchor="center"),
                    ),
                )
            )

            # self.segment_scores.

        #     _txt = f"{round(100 * _mean)}"
        #     self.canvas.create_text(*center, text=_txt, anchor="center", font=("Arial", 18))
        # self.canvas.create_text(256, 256, text="50", anchor="center", font=("Arial", 18))

    #     _mask = segment_mask(self.activities, seg, self.azimuth_angles)
    #     # _mask = segment_mask(self.activities, seg)
    #     _mean = np.average(self.activities[_mask])
    #     _txt = f"{round(100 * _mean)}"
    #     self.canvas.create_text(*center, text=_txt, anchor="center", font=("Arial", 18))
    #

    # self.canvas_3 = Canvas(self, CanvasState())
    # self.canvas_3.grid(row=1, column=0, columnspan=2)
    # self.x = Image(
    #     self.canvas_3, ImageState(state.activity_image, ImageStyle(fit="fill"))
    # )

    def horizontal_line(self, relative_position: FloatState, color: str) -> Line:
        start = compute(
            [relative_position, self.image._state, self.canvas._state],
            lambda: PointState(
                *self.image.to_canvas(
                    0, relative_position.value * self.image._state.data.value.shape[0]
                )
            ),
        )
        end = compute(
            [relative_position, self.image._state, self.canvas._state],
            lambda: PointState(
                *self.image.to_canvas(
                    self.image._state.data.value.shape[1],
                    relative_position.value * self.image._state.data.value.shape[0],
                )
            ),
        )
        line = Line(
            self.canvas,
            state=LineState(
                data=LineData(start, end),
                style=LineStyle(
                    color=color, width=2, dash=ListState([IntState(8), IntState(5)])
                ),
            ),
        )
        line.tag_bind(
            "<B1-Motion>",
            lambda ev, _: relative_position.set(
                self.image.to_image_continuous(ev.x, ev.y)[1]
                / self.image._state.data.value.shape[0]
            ),
        )
