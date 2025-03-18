import io
import math
import tkinter as tk
from tkinter import filedialog
from tkinter import ttk

import cv2 as cv
import numpy as np
from numpy.typing import NDArray
import scipy

from reacTk.state import PointState
from reacTk.state.util import to_tk_var
from reacTk.widget.chechbox import Checkbox, CheckBoxProperties, CheckBoxState
from reacTk.widget.canvas import Canvas, CanvasState
from reacTk.widget.canvas.image import Image, ImageData, ImageState, ImageStyle
from reacTk.widget.canvas.text import Text, TextData, TextState, TextStyle
from widget_state import (
    HigherOrderState,
    IntState,
    computed,
    compute,
    StringState,
    ListState,
    BoolState,
)

from ..colormap import colormaps

from .sampling import cartesian_grid
from .segment import SEGMENTS, segment_vertices, segment_center, segment_mask


def draw_segments_grid(polar_map: NDArray) -> NDArray:
    """
    Note: we use OpenCV to draw the lines instead of tk
    because it supports anti aliasing which looks a lot better
    """
    cy, cx = np.array(polar_map.shape[:2]) // 2
    for radius in np.array([0.25, 0.5, 0.75]) * polar_map.shape[0] // 2:
        polar_map = cv.circle(
            polar_map,
            (cx, cy),
            radius=round(radius),
            color=(0, 0, 0),
            thickness=1,
            lineType=cv.LINE_AA,
        )
    # draw the outermost circle a pixel closer to cover
    # aliasing artifacts
    polar_map = cv.circle(
        polar_map,
        (cx, cy),
        radius=polar_map.shape[0] // 2 - 1,
        color=(0, 0, 0),
        thickness=1,
        lineType=cv.LINE_AA,
    )

    for segment in SEGMENTS[:-1]:
        vertices = segment_vertices(segment, polar_map.shape[0] // 2)
        polar_map = cv.line(
            polar_map,
            vertices[0],
            vertices[1],
            color=(0, 0, 0),
            thickness=1,
            lineType=cv.LINE_AA,
        )

    return polar_map


class PolarMapState(HigherOrderState):

    def __init__(self, radial_activities: ImageData):
        super().__init__()

        self.draw_segment_scores = BoolState(True)
        self.colormap = StringState("prism")

        self.n_samples = IntState(256)
        self.radial_activities = radial_activities

        self.segment_scores = ListState([IntState(0) for i in range(len(SEGMENTS))])
        self.radial_activities.on_change(self.compute_segment_scores, trigger=True)

        self._validate_computed_states()

    @computed
    def image(
        self,
        radial_activities: ImageData,
        n_samples: IntState,
        draw_segment_scores: BoolState,
        colormap: StringState,
    ) -> ImageData:
        grid = cartesian_grid(self.radial_activities.value, n_samples=n_samples.value)
        image = scipy.ndimage.map_coordinates(
            self.radial_activities.value, grid, order=3, mode="constant", cval=0.0
        )

        if image.max() == 0 or math.isnan(image.max()):
            return ImageData(
                np.zeros((n_samples.value, n_samples.value, 3), dtype=np.uint8)
            )

        image = image / image.max()
        image = (255 * image).astype(np.uint8)
        # apply colormap
        image = colormaps[colormap.value][image]
        # mask the polar map circle because some colormaps are not black at zero
        mask = np.zeros(image.shape[:2], np.uint8)
        mask = cv.circle(mask, (mask.shape[1] // 2, mask.shape[0] // 2), radius=mask.shape[0] // 2, color=255, thickness=-1)
        image = cv.bitwise_and(image, image, mask=mask)
        # Note: we should resize before drawing the segments grid, so that lines are sharp
        image = cv.resize(image, (512, 512))


        if draw_segment_scores.value:
            image = draw_segments_grid(image)

        # image = cv.cvtColor(image, cv.COLOR_BGR2RGB)
        return ImageData(image)

    def compute_segment_scores(self, radial_activities: ImageData) -> None:
        radial_activities = radial_activities.value

        for segment, segment_score in zip(SEGMENTS, self.segment_scores):
            mask = segment_mask(radial_activities, segment)
            activity = radial_activities[mask]

            if activity.max() == 0 or math.isnan(activity.max()):
                score = 0
            else:
                score = round(100 * np.average(activity))

            segment_score.value = score


polar_map_state = PolarMapState(np.zeros((32, 128)))


class PolarMap(ttk.Frame):

    def __init__(self, parent: tk.Widget, state: PolarMapState):
        super().__init__(parent)

        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=10)
        self.rowconfigure(1, weight=1)

        self.state = state

        self.canvas = Canvas(self, CanvasState())
        self.canvas.grid(column=0, row=0, sticky="nswe", columnspan=2)
        self.image = Image(self.canvas, ImageState(self.state.image))
        self.segment_score_texts = []
        self.state.draw_segment_scores.on_change(
            self.draw_segment_score_texts, trigger=True
        )

        self.draw_segments_checkbox = Checkbox(
            self,
            CheckBoxState(
                self.state.draw_segment_scores,
                CheckBoxProperties(label="Draw Segments"),
            ),
        )
        self.draw_segments_checkbox.grid(column=0, row=1)

        self.context_menu = tk.Menu(self, tearoff=False)
        self.context_menu.add_command(label="Save as", command=self.save_canvas_content)
        self.canvas.bind("<Button-3>", self.popup_menu)

        self.options = tk.OptionMenu(self, to_tk_var(self.state.colormap), *colormaps.keys())
        self.options.grid(column=1, row=1)

    def draw_segment_score_texts(self, active: BoolState) -> None:
        if not active.value:
            for text in self.segment_score_texts:
                text.delete()
            self.segment_score_texts.clear()
            return

        for segment, segment_score in zip(SEGMENTS, self.state.segment_scores):
            text_position = compute(
                [self.image._state],
                lambda segment=segment: PointState(
                    *self.image.to_canvas(
                        *segment_center(
                            segment, self.image._state.data.value.shape[0] // 2
                        )
                    )
                ),
            )
            text = segment_score.transform(lambda s: StringState(str(s.value)))
            self.segment_score_texts.append(
                Text(
                    self.canvas,
                    TextState(
                        TextData(text, text_position),
                        style=TextStyle(color="white", anchor="center", font_size=20),
                    ),
                )
            )

    def popup_menu(self, event):
        try:
            self.context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.context_menu.grab_release()

    def save_canvas_content(self):
        filename = filedialog.asksaveasfilename()

        """
        We directly use the numpy array and re-draw segment scores with OpenCV
        if necessary, because the font looks terrible of the image is retrieved from
        the canvas via `postscript`.
        """
        img = self.state.image.value
        img = cv.cvtColor(img, cv.COLOR_RGB2BGR)
        if self.state.draw_segment_scores.value:
            for segment, segment_score in zip(SEGMENTS, self.state.segment_scores):
                text_position = segment_center(segment, img.shape[0] // 2)
                text_position = (text_position[0] - 20, text_position[1] + 10)
                text = f"{segment_score.value}"
                cv.putText(img, text, text_position, fontFace=cv.FONT_HERSHEY_SIMPLEX, lineType=cv.LINE_AA, fontScale=1.0, color=(255, 255, 255), thickness=2)

        cv.imwrite(filename, img)


