import time

import cv2 as cv
import numpy as np
import scipy
import SimpleITK as sitk
from reacTk.decorator import asynchron
from reacTk.widget.canvas.image import ImageData
from widget_state import HigherOrderState, computed, IntState, FloatState

from ..widget.slice_view import SITKData
from ..util import pad_crop, get_empty_image

from .sampling import polar_grid, cartesian_grid
from .segment import SEGMENTS, segment_vertices


class AppState(HigherOrderState):
    def __init__(self):
        super().__init__()

        # target range the image should span in mm
        self.input_image = SITKData(get_empty_image(spacing=(10.0, 10.0, 10.0)))
        self.target_range = 150

        self.pos_rad = FloatState(0.0)
        self.pos_cylindrical = FloatState(0.0)
        self.image.on_change(lambda _: self.pos_rad.set(0.5))
        self.image.on_change(lambda _: self.pos_cylindrical.set(0.81))

        self.radial_activities = ImageData(np.zeros((128, 32), dtype=np.uint8))
        self.pos_rad.on_change(lambda _: self.compute_radial_activities())
        self.pos_cylindrical.on_change(lambda _: self.compute_radial_activities())
        self.sa_image.on_change(lambda _: self.compute_radial_activities())

        self._validate_computed_states()

    def reset(self):
        pass

    @computed
    def image(self, input_image: SITKData, target_range: IntState) -> SITKData:
        target_shape = round(target_range.value / input_image.value.GetSpacing()[0])
        target_shape = (target_shape,) * 3
        return SITKData(pad_crop(input_image.value, target_shape=target_shape))

    @computed
    def sa_image(self, image: SITKData):
        sitk_img = image.value[:]
        sitk_img = sitk.PermuteAxes(sitk_img, (2, 0, 1))
        return SITKData(sitk_img)

    @computed
    def central_slice(self, image: SITKData) -> ImageData:
        img = image.value
        img = sitk.GetArrayFromImage(img)

        if img.max() == 0:
            return ImageData(np.zeros((128, 128, 3), dtype=np.uint8))

        img = img / img.max()
        img = img[img.shape[0] // 2]
        img = (255 * img).astype(np.uint8)
        img = cv.applyColorMap(img, cv.COLORMAP_INFERNO)
        img = cv.cvtColor(img, cv.COLOR_BGR2RGB)
        return ImageData(img)

    @asynchron
    def compute_radial_activities(self) -> None:
        img = sitk.GetArrayFromImage(self.sa_image.value)
        if img.max() == 0:
            return

        radii = np.arange(0, img.shape[1] / 2, 0.2)
        azimuth_angles = np.deg2rad(np.arange(0, 360, 1))
        polar_angles = np.deg2rad(np.arange(0, 90, (90 / 10) - 0.001))

        cz = round(self.pos_rad.value * img.shape[0])
        n_cylindrical = round(self.pos_cylindrical.value * img.shape[0]) - cz

        since = time.time()
        grid = polar_grid(img, radii, azimuth_angles, polar_angles, center_z=cz)

        since = time.time()
        polar_rep = scipy.ndimage.map_coordinates(img, grid, order=3)
        # print(f" - Polar rep shape {polar_rep.shape}")
        polar_rep = polar_rep[: len(polar_angles) + n_cylindrical]
        # print(f" - Polar rep shape after {polar_rep.shape} - {n_cylindrical=}, {cz=}")

        activities = np.max(polar_rep, axis=1)
        # print(f" - Activites shape {polar_rep.shape}")

        activities_apex = activities[: len(polar_angles)]
        activities_other = activities[len(polar_angles) :]
        activities_apex = cv.resize(
            activities_apex, (activities_apex.shape[1], activities_other.shape[0] // 3)
        )
        activities = np.concat([activities_apex, activities_other], axis=0)
        activities = (activities - activities.min()) / (
            activities.max() - activities.min()
        )

        self.radial_activities.set(activities)

    @computed
    def activity_image(self, radial_activities: ImageData):
        img = radial_activities.value
        img = (255 * img).astype(np.uint8)
        img = cv.applyColorMap(img, cv.COLORMAP_INFERNO)
        img = cv.cvtColor(img, cv.COLOR_BGR2RGB)
        return ImageData(img)

    @computed
    def polar_map(self, radial_activities: ImageData):
        grid = cartesian_grid(self.radial_activities.value, n_samples=256)
        pm = scipy.ndimage.map_coordinates(
            self.radial_activities.value, grid, order=3, mode="constant", cval=0.0
        )

        if pm.max() == 0:
            return ImageData(np.zeros((128, 128, 3), dtype=np.uint8))
        pm = pm / pm.max()
        # pm = (pm - pm.min()) / /
        pm = (255 * pm).astype(np.uint8)
        pm = cv.applyColorMap(pm, cv.COLORMAP_INFERNO)
        pm = cv.resize(pm, (512, 512))
        pm = draw_segments_grid(pm)
        pm = cv.cvtColor(pm, cv.COLOR_BGR2RGB)
        return ImageData(pm)


def draw_segments_grid(polar_map):
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
