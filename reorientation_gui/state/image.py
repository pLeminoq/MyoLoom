from typing import Optional, Tuple

import numpy as np
import SimpleITK as sitk

from reorientation_gui.state.lib import ObjectState, StringState, State
from reorientation_gui.state.reorientation import ReorientationState
from reorientation_gui.util import (
    get_empty_image,
    load_image,
    square_pad,
    transform_image,
)


class ImageState(ObjectState):

    def __init__(self, value: np.array):
        super().__init__(value)


class SITKImageState(ObjectState):

    def __init__(self, value: sitk.Image):
        super().__init__(value)


class TransformedSITKImageState(SITKImageState):

    def __init__(
        self,
        _sitk_img_state,
        reorientation_state: Optional[ReorientationState] = None,
        permutation: Tuple[int, int, int] = (0, 1, 2),
        flip_axes: Tuple[bool, bool, bool] = (False, False, False),
    ):
        super().__init__(
            transform_image(
                _sitk_img_state.value, reorientation_state, permutation, flip_axes
            )
        )

        self.reorientation_state = reorientation_state
        self.permutation = permutation
        self.flip_axes = flip_axes
        self._sitk_img_state = _sitk_img_state

        self._sitk_img_state.on_change(self.internal_update)
        if self.reorientation_state is not None:
            self.reorientation_state.on_change(self.internal_update)

    def internal_update(self, *args):
        self.value = transform_image(
            self._sitk_img_state.value,
            self.reorientation_state,
            self.permutation,
            self.flip_axes,
        )
        self.notify_change()


class FileImageState(State):

    def __init__(self, filename: str = ""):
        super().__init__(verify_change=False)

        self.filename = StringState(filename)
        self.sitk_img_state = SITKImageState(self.load_image(self.filename.value))

        self.filename.on_change(self.on_filename_change)

    def load_image(self, filename: str):
        if filename == "":
            return get_empty_image()

        return square_pad(load_image(filename))

    def on_filename_change(self, state: StringState):
        self.sitk_img_state.update(self.load_image(state.value))
        self.notify_change()
