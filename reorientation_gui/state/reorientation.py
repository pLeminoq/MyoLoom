from typing import Optional, List, Tuple

import numpy as np
import SimpleITK as sitk

from reorientation_gui.state.lib import State, IntState, FloatState


class ReorientationState(State):
    """
    State keeping track of the reorientation parameters.

    TODO: correct angles?
    Reorientation is achieved by centering the heart and rotating around z and x angles.
    Thus, the reorientation is parameterized by the hearts center and these angles.
    The heart center is given in pixel coordinates.
    """

    def __init__(
        self,
        angle_x: float,
        angle_y: float,
        angle_z: float,
        center_x: int,
        center_y: int,
        center_z: int,
    ):
        super().__init__()

        self.angle_x = FloatState(angle_x)
        self.angle_y = FloatState(angle_y)
        self.angle_z = FloatState(angle_z)
        self.center_x = IntState(center_x)
        self.center_y = IntState(center_y)
        self.center_z = IntState(center_z)

        self.angle_x.on_change(lambda _: self.notify_change(ignore_change=True))
        self.angle_y.on_change(lambda _: self.notify_change(ignore_change=True))
        self.angle_z.on_change(lambda _: self.notify_change(ignore_change=True))
        self.center_x.on_change(lambda _: self.notify_change(ignore_change=True))
        self.center_y.on_change(lambda _: self.notify_change(ignore_change=True))
        self.center_z.on_change(lambda _: self.notify_change(ignore_change=True))


    def apply(self, sitk_image: sitk.Image, translation: str = "xyz", rotation: str = "xyz") -> sitk.Image:
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
        # create a copy so that the original is not modified
        reoriented = sitk_image[:]

        #TODO: compute center from image
        center_image = list(map(lambda x: x // 2, sitk_image.GetSize())) 
        center_heart = [self.center_x.value, self.center_y.value, self.center_z.value]

        center_image = np.array(sitk_image.TransformContinuousIndexToPhysicalPoint(center_image))
        center_heart = np.array(sitk_image.TransformContinuousIndexToPhysicalPoint(center_heart))
        offset = center_heart - center_image
        offset = (
            offset[0] if "x" in translation else 0.0,
            offset[1] if "y" in translation else 0.0,
            offset[2] if "z" in translation else 0.0,
        )

        translation = sitk.TranslationTransform(3, offset)
        rotation = sitk.Euler3DTransform(
            center_image,
            self.angle_x.value if "x" in rotation else 0.0,
            self.angle_y.value if "y" in rotation else 0.0,
            self.angle_z.value if "z" in rotation else 0.0,
        )
        return sitk.Resample(
            reoriented,
            reoriented,
            sitk.CompositeTransform([translation, rotation]),
            sitk.sitkLinear,
            0.0,
        )

    def update(
        self,
        angle_x: Optional[float] = None,
        angle_y: Optional[float] = None,
        angle_z: Optional[float] = None,
        heart_x: Optional[float] = None,
        heart_y: Optional[float] = None,
        heart_z: Optional[float] = None,
    ):
        """
        Update the reorientation state and notify the change.

        Parameters
        ----------
        angle_x: float
            new angle for x-rotation
        angle_y: float
            new angle for y-rotation
        angle_z: float
            new angle for z-rotation
        heart_x: float
            new heart position along x-axis
        heart_y: float
            new heart position along y-axis
        heart_z: float
            new heart position along z-axis
        """
        self.angle_x = angle_x if angle_x is not None else self.angle_x
        self.angle_y = angle_y if angle_y is not None else self.angle_y
        self.angle_z = angle_z if angle_z is not None else self.angle_z

        self.center_heart[0] = (
            heart_x if heart_x is not None else self.center_heart[0]
        )
        self.center_heart[1] = (
            heart_y if heart_y is not None else self.center_heart[1]
        )
        self.center_heart[2] = (
            heart_z if heart_z is not None else self.center_heart[2]
        )

        self.notify_change()
