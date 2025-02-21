import time

import cv2 as cv
import numpy as np
import scipy
import SimpleITK as sitk
from reacTk.decorator import asynchron
from reacTk.widget.canvas.image import ImageData
from widget_state import HigherOrderState, computed, NumberState

from ..widget.slice_view import SITKData
from ..util import pad_crop, get_empty_image

from .config_view import ConfigViewState
from .sampling import polar_grid, cartesian_grid
from .segment import SEGMENTS, segment_vertices
from .util import weight_polar_rep


class AppState(HigherOrderState):
    def __init__(self):
        super().__init__()

        # target range the image should span in mm
        self.input_image = SITKData(get_empty_image(spacing=(10.0, 10.0, 10.0)))
        self.target_range = 200

        self.config_view_state = ConfigViewState(self.sa_image)

        self.radial_activities = ImageData(np.zeros((128, 32), dtype=np.uint8))
        self.sa_image.on_change(lambda _: self.compute_radial_activities())
        self.config_view_state.center_z.on_change(lambda _: self.compute_radial_activities())
        self.config_view_state.pos_line_lateral.on_change(lambda _: self.compute_radial_activities())
        self.config_view_state.pos_line_septal.on_change(lambda _: self.compute_radial_activities())
        self.config_view_state.weighting.on_change(lambda _: self.compute_radial_activities())

        self._validate_computed_states()

    def reset(self):
        pass

    @computed
    def image(self, input_image: SITKData, target_range: NumberState) -> SITKData:
        target_shape = round(target_range.value / input_image.value.GetSpacing()[0])
        target_shape = (target_shape,) * 3
        return SITKData(pad_crop(input_image.value, target_shape=target_shape))

    @computed
    def sa_image(self, image: SITKData):
        sitk_img = image.value[:]
        sitk_img = sitk.PermuteAxes(sitk_img, (2, 0, 1))
        center = sitk_img.TransformContinuousIndexToPhysicalPoint(
            np.array(sitk_img.GetSize()) / 2.0
        )
        sitk_img = sitk.Resample(
            sitk_img,
            sitk.Euler3DTransform(center, 0.0, np.rad2deg(-90), 0.0),
            sitk.sitkLinear,
            0.0,
        )
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

        sigma = 3
        radii_step = 0.2
        radii = np.arange(0, img.shape[1] / 2, radii_step)
        azimuth_angles = np.deg2rad(np.arange(0, 360, 1))
        polar_angles = np.deg2rad(np.arange(0, 90, (90 / 10) - 0.001))

        grid = polar_grid(img, radii, azimuth_angles, polar_angles, **self.config_view_state.sampling_params())

        polar_rep = scipy.ndimage.map_coordinates(img, grid, order=3)

        if self.config_view_state.weighting.value:
            pixel_size_mm = self.sa_image.value.GetSpacing()[0] * radii_step
            polar_rep = weight_polar_rep(polar_rep, pixel_size_mm=pixel_size_mm, sigma=sigma)

        radial_activities = np.max(polar_rep, axis=1)

        # The polar rep can be/is likely imbalanced along the z axis.
        # This is because it contains n=#polar_angles slices for the apex and m slices for the cylindrical region.
        # According to the polar map model m should be 3*n.
        # This is ensured by the following code.
        activities_apex = radial_activities[: len(polar_angles)]
        activities_other = radial_activities[len(polar_angles) :]
        activities_other = cv.resize(
            activities_other, (activities_other.shape[1], activities_apex.shape[0] * 3)
        )
        radial_activities = np.concat([activities_apex, activities_other], axis=0)

        # normalize the activities
        if radial_activities.max() > 0.0:
            radial_activities = radial_activities / radial_activities.max()

        self.radial_activities.set(radial_activities)
    #
    # @computed
    # def activity_image(self, radial_activities: ImageData):
    #     img = radial_activities.value
    #     img = (255 * img).astype(np.uint8)
    #     img = cv.applyColorMap(img, cv.COLORMAP_INFERNO)
    #     img = cv.cvtColor(img, cv.COLOR_BGR2RGB)
    #     return ImageData(img)
