import numpy as np
import SimpleITK as sitk

from reorientation_gui.state.lib import (
    computed_state,
    FloatState,
    HigherState,
    IntState,
    ObjectState,
    StringState,
)
from reorientation_gui.state.reorientation import (
    AngleState,
    CenterState,
    ReorientationState,
)
from reorientation_gui.state.resolution import ResolutionState
from reorientation_gui.util import load_image, square_pad, get_empty_image


class AppState(HigherState):

    def __init__(
        self,
    ):
        super().__init__()

        self.filename_state = StringState("")
        self.normalization_state = FloatState(1.0)
        self.sitk_img_state = self.sitk_img_state(self.filename_state)
        self.sitk_img_saggital_state = self.sitk_img_saggital_state(self.sitk_img_state)

        size = self.sitk_img_state.value.GetSize()
        self.reorientation_state = ReorientationState(
            angle_state=AngleState(0.0, 0.0, 0.0),
            center_state=CenterState(size[0] // 2, size[1] // 2, size[2] // 2),
        )

        self.resolution_state = ResolutionState(
            width=self.sitk_img_state.value.GetSize()[0],
            height=self.sitk_img_state.value.GetSize()[1],
        )
        self.rectangle_size_state = IntState(0)

        self.img_reoriented_state = self.img_reoriented_state(
            self.sitk_img_state, self.reorientation_state
        )
        self.img_hla_state = self.img_reoriented_state
        self.img_sa_state = self.img_sa_state(self.img_reoriented_state)
        self.img_vla_state = self.img_vla_state(self.img_reoriented_state)

        self.filename_state.on_change(lambda _: self.reset_reorientation())

    def reset_reorientation(self):
        size = self.sitk_img_state.value.GetSize()
        with self.reorientation_state as state:
            state.angle_state.set(0.0, 0.0, 0.0)
            state.center_state.set(size[0] // 2, size[1] // 2, size[2] // 2)

    @computed_state
    def sitk_img_state(self, filename_state: StringState) -> ObjectState:
        if filename_state.value == "":
            return ObjectState(get_empty_image())

        return ObjectState(square_pad(load_image(filename_state.value)))

    @computed_state
    def sitk_img_saggital_state(self, sitk_img_state: ObjectState) -> ObjectState:
        return ObjectState(sitk.PermuteAxes(sitk_img_state.value[:], (1, 2, 0)))

    @computed_state
    def img_reoriented_state(
        self, sitk_img_state: ObjectState, reorientation_state: ReorientationState
    ) -> ObjectState:
        """
        Apply the reorientation to the image.

        Parameters
        ----------
        translation: str
            define along which axes to translate the image, default is "xyz"
        rotation: str
            deinfe along which axes to rotate the image, default is "xz",

        Returns
        -------
        sitk.Image
        """
        reoriented = sitk_img_state.value[:]

        center_image = list(map(lambda x: x // 2, reoriented.GetSize()))
        center_heart = list(reorientation_state.center_state.values())

        center_image = np.array(
            reoriented.TransformContinuousIndexToPhysicalPoint(center_image)
        )
        center_heart = np.array(
            reoriented.TransformContinuousIndexToPhysicalPoint(center_heart)
        )
        offset = center_heart - center_image

        translation = sitk.TranslationTransform(3, offset)
        rotation = sitk.Euler3DTransform(
            center_image, *reorientation_state.angle_state.values()
        )
        resampled = sitk.Resample(
            reoriented,
            reoriented,
            sitk.CompositeTransform([translation, rotation]),
            sitk.sitkLinear,
            0.0,
        )
        return ObjectState(resampled)

    @computed_state
    def img_sa_state(self, img_reoriented_state: ObjectState) -> ObjectState:
        _img = img_reoriented_state.value[:]
        _img = sitk.PermuteAxes(_img, (2, 0, 1))
        return ObjectState(_img)

    @computed_state
    def img_vla_state(self, img_reoriented_state: ObjectState) -> ObjectState:
        _img = img_reoriented_state.value[:]
        _img = sitk.PermuteAxes(_img, (1, 2, 0))
        _img = sitk.Flip(_img, (True, True, False))
        return ObjectState(_img)
