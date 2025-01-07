import time

import numpy as np
import SimpleITK as sitk
from widget_state import (
    FloatState,
    HigherOrderState,
    IntState,
    StringState,
    computed,
)

from reacTk.decorator import asynchron

from ..widget.slice_view import SITKData
from ..util import load_image, square_pad, get_empty_image
from .reorientation import (
    AngleState,
    CenterState,
    ReorientationState,
)
from .resolution import ResolutionState


class AppState(HigherOrderState):
    def __init__(
        self,
    ):
        super().__init__()

        self.filename = StringState("")
        self.clip_percentage = FloatState(1.0)
        self.rectangle_size = IntState(8)

        self.reorientation = ReorientationState(
            angle=AngleState(0.0, 0.0, 0.0),
            center=CenterState(0.0, 0.0, 0.0),
        )

        self.filename.on_change(lambda _: self.reset_reorientation())

    def reset_reorientation(self):
        """
        Reset the reorientation (no translation and no rotation).

        This is typically done when a new image is loaded
        """
        size = self.sitk_img.value.GetSize()
        center = (size[0] / 2.0, size[1] / 2.0, size[2] / 2.0)
        physical_center = self.sitk_img.value.TransformContinuousIndexToPhysicalPoint(
            center
        )
        with self.reorientation as state:
            state.angle.set(0.0, 0.0, 0.0)
            state.center.set(size[0] / 2.0, size[1] // 2.0, size[2] / 2.0)

    @computed
    def sitk_img(self, filename: StringState) -> SITKData:
        if filename.value == "":
            return SITKData(get_empty_image())
        return SITKData(square_pad(load_image(filename.value)))

    @computed
    def sitk_img_saggital(self, sitk_img: SITKData) -> SITKData:
        return SITKData(sitk.PermuteAxes(sitk_img.value[:], (1, 2, 0)))

    @computed
    def img_reoriented(
        self, sitk_img: SITKData, reorientation: ReorientationState
    ) -> SITKData:
        since = time.time()
        reoriented = sitk_img.value[:]

        center_image = list(map(lambda x: x // 2, reoriented.GetSize()))
        center_heart = list(reorientation.center.values())

        center_image = np.array(
            reoriented.TransformContinuousIndexToPhysicalPoint(center_image)
        )
        center_heart = np.array(
            reoriented.TransformContinuousIndexToPhysicalPoint(center_heart)
        )
        offset = center_heart - center_image

        translation = sitk.TranslationTransform(3, offset)
        rotation = sitk.Euler3DTransform(center_image, *reorientation.angle.values())

        resampled = sitk.Resample(
            reoriented,
            reoriented,
            sitk.CompositeTransform([translation, rotation]),
            sitk.sitkLinear,
            0.0,
        )
        return SITKData(resampled)

    @computed
    def img_sa(self, img_reoriented: SITKData) -> SITKData:
        if img_reoriented.value is None:
            return SITKData(get_empty_image())

        _img = img_reoriented.value[:]
        _img = sitk.PermuteAxes(_img, (2, 0, 1))
        return SITKData(_img)

    @computed
    def img_vla(self, img_reoriented: SITKData) -> SITKData:
        if img_reoriented.value is None:
            return SITKData(get_empty_image())

        _img = img_reoriented.value[:]
        _img = sitk.PermuteAxes(_img, (1, 2, 0))
        _img = sitk.Flip(_img, (True, True, False))
        return SITKData(_img)
