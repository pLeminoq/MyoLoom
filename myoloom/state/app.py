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
from ..util import load_image, square_pad, get_empty_image, is_short_axis
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

        self.sitk_img = SITKData(get_empty_image())

        self.reorientation = ReorientationState(
            angle=AngleState(0.0, 0.0, 0.0),
            center=CenterState(0.0, 0.0, 0.0),
        )

        self.filename.on_change(lambda _: self.load_image())
        self.sitk_img.on_change(lambda _: self.reset_reorientation())

    def reset_reorientation(self):
        """
        Reset the reorientation (no translation and no rotation).

        This is typically done when a new image is loaded
        """
        size = self.sitk_img.value.GetSize()
        with self.reorientation as state:
            state.angle.set(0.0, 0.0, 0.0)
            state.center.set(size[0] / 2.0, size[1] / 2.0, size[2] / 2.0)

    def load_image(self):
        if self.filename.value == "":
            self.sitk_img.value = get_empty_image()
            return

        if is_short_axis(self.filename.value):
            """
            To correctly display a short-axis image, we have to rotate the image
            back to a transversal view and subsequently, apply the rotation angles
            to the reorientation state.
            """
            sitk_img = load_image(self.filename.value)

            # retrieve image center for rotation (around the center)
            center_image_idx = list(map(lambda x: x / 2, sitk_img.GetSize()))
            center_image_phys = sitk_img.TransformContinuousIndexToPhysicalPoint(
                center_image_idx
            )

            # retrieve rotation matrix (from transversal to short-axis)
            rot_mat = np.array(sitk_img.GetDirection()).reshape((3, 3))

            # rotate to transversal view (inverse rotation)
            euler_trans = sitk.Euler3DTransform(center_image_phys)
            euler_trans.SetMatrix(rot_mat.T.flatten())
            sitk_img = sitk.Resample(
                sitk_img,
                euler_trans,
                sitk.sitkLinear,
                0.0,
            )
            # resample does not update the Direction, so we set this manually
            sitk_img.SetDirection((1, 0, 0, 0, 1, 0, 0, 0, 1))

            # update image
            self.sitk_img.value = sitk_img

            # update angles in reorientation state
            euler_trans.SetMatrix(rot_mat.flatten())
            self.reorientation.angle.x.value = euler_trans.GetAngleX() + np.deg2rad(
                90
            )  # we have to revert the -90° rotation around x which rotates a HLA into an SA image
            self.reorientation.angle.z.value = euler_trans.GetAngleZ()
            return

        self.sitk_img.value = square_pad(load_image(self.filename.value))
        self.reset_reorientation()

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
