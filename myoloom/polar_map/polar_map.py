import math
       
import cv2 as cv
import numpy as np
from numpy.typing import NDArray
import scipy
import tkinter as tk

from reacTk.state import PointState
from reacTk.widget.canvas import Canvas, CanvasState
from reacTk.widget.canvas.image import Image, ImageData, ImageState, ImageStyle
from reacTk.widget.canvas.text import Text, TextData, TextState, TextStyle
from widget_state import HigherOrderState, IntState, computed, compute, StringState, ListState

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

        self.n_samples = IntState(256)
        self.radial_activities = radial_activities

        self.segment_scores = ListState([IntState(0) for i in range(len(SEGMENTS))])
        self.radial_activities.on_change(self.compute_segment_scores, trigger=True)

        self._validate_computed_states()

    @computed
    def image(self, radial_activities: ImageData, n_samples: IntState) -> ImageData:
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
        image = cv.applyColorMap(image, cv.COLORMAP_INFERNO)
        # Note: we should resize before drawing the segments grid, so that lines are sharp
        image = cv.resize(image, (512, 512))
        image = draw_segments_grid(image)
        image = cv.cvtColor(image, cv.COLOR_BGR2RGB)
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

class PolarMap(Canvas):

    def __init__(self, parent: tk.Widget, state: PolarMapState):
        super().__init__(parent, CanvasState())

        self.image = Image(self, ImageState(state.image))
        self.segment_scores = []
        for segment, segment_score in zip(SEGMENTS, state.segment_scores):
            text_position = compute(
                [self.image._state, self._state],
                lambda segment=segment: PointState(
                    *self.image.to_canvas(
                        *segment_center(
                            segment, self.image._state.data.value.shape[0] // 2
                        )
                    )
                ),
            )
            text = segment_score.transform(lambda s: StringState(str(s.value)))
            self.segment_scores.append(
                Text(
                    self,
                    TextState(
                        TextData(text, text_position),
                        style=TextStyle(color="white", anchor="center"),
                    ),
                )
            )
