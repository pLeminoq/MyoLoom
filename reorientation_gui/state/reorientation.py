from typing import Optional, List, Tuple

import numpy as np
import SimpleITK as sitk

from reorientation_gui.state.lib import State


def get_physical_center(sitk_image: sitk.Image):
    """
    Get the center point of an SITK image in physical coordinates.

    Parameters
    ----------
    sitk_image: sitk.Image

    Returns
    -------
    tuple of float
    """
    size = sitk_image.GetSize()
    center = tuple(map(lambda x: x // 2, size))
    return sitk_image.TransformIndexToPhysicalPoint(center)


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
        sitk_image: sitk.Image,
        angle_x: float = 0.0,
        angle_y: float = 0.0,
        angle_z: float = 0.0,
        heart_center: Optional[List[int]] = None,
    ):
        super().__init__()

        self.sitk_image = sitk_image
        self.center_image = tuple(map(lambda x: x // 2, self.sitk_image.GetSize()))

        self.angle_x = angle_x
        self.angle_y = angle_y
        self.angle_z = angle_z
        self.center_heart = list(
            heart_center
            if heart_center is not None
            else list(self.center_image) 
        )

    def apply(self, translation: str = "xyz", rotation: str = "xyz") -> sitk.Image:
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
        reoriented = self.sitk_image[:]

        center_image = np.array(self.sitk_image.TransformIndexToPhysicalPoint(self.center_image))
        center_heart = np.array(self.sitk_image.TransformIndexToPhysicalPoint(self.center_heart))
        offset = center_heart - center_image
        offset = (
            offset[0] if "x" in translation else 0.0,
            offset[1] if "y" in translation else 0.0,
            offset[2] if "z" in translation else 0.0,
        )

        translation = sitk.TranslationTransform(3, offset)
        rotation = sitk.Euler3DTransform(
            center_image,
            self.angle_x if "x" in rotation else 0.0,
            self.angle_y if "y" in rotation else 0.0,
            self.angle_z if "z" in rotation else 0.0,
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
        heart_x: Optional[int] = None,
        heart_y: Optional[int] = None,
        heart_z: Optional[int] = None,
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

        tmp = self.center_heart[:]
        self.center_heart[0] = (
            heart_x if heart_x is not None else self.center_heart[0]
        )
        self.center_heart[1] = (
            heart_y if heart_y is not None else self.center_heart[1]
        )
        self.center_heart[2] = (
            heart_z if heart_z is not None else self.center_heart[2]
        )
        print(f"Update heart center from {tmp} to {self.center_heart} because of {(heart_x, heart_y, heart_z)}")

        self.notify_change()
