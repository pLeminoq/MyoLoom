"""
Utility functions that mainly are about image operations.
"""

import math
from typing import Optional, Tuple

import numpy as np
from PIL import Image, ImageTk
import SimpleITK as sitk

from reorientation_gui.state.reorientation import ReorientationState


def get_empty_image(size: Tuple[int, int, int] = (128, 128, 128)) -> sitk.Image:
    """
    Create an empty SITK image.

    Parameters
    ----------
    size: tuple of int
        size of the created image

    Returns
    -------
    sitk.Image
    """
    return sitk.Image(size, sitk.sitkFloat64)


def load_image(filename: str) -> sitk.Image:
    """
    Load an SITK image from a filename.

    This operations
      * casts the image as float,
      * ensures that the stacking direction of slices is positive,
      * and applies a custom scaling used by Siemens SPECT devices


    Parameters
    ----------
    filename: str

    Returns
    -------
    sitk.Image
    """
    sitk_reader = sitk.ImageFileReader()
    sitk_reader.LoadPrivateTagsOn()
    sitk_reader.SetFileName(filename)

    # store the original containing meta information
    _sitk_img = sitk_reader.Execute()

    # on casting and other operations the meta information is removed
    sitk_img = _sitk_img[:]
    sitk_img = sitk.Cast(sitk_img, sitk.sitkFloat64)

    try:
        """
        Change the stacking direction of slices in an image based
        on the tag "SpacingBetweenSlices=0x00180088".
        """
        spacing_between_slices = float(_sitk_img.GetMetaData("0018|0088"))
        if spacing_between_slices < 0:
            sitk_img = sitk_img[:, :, ::-1]
    except AttributeError:
        pass

    try:
        """
        Rescale if the header contains the privat tag "PixelScaleFactor=0x00331038".
        """
        scale = float(_sitk_img.GetMetaData("0033|1038"))
        sitk_img = 1.0 * sitk_img / scale
    except AttributeError:
        pass

    return sitk_img


def square_pad(sitk_img: sitk.Image, pad_value: float = 0.0) -> sitk.Image:
    """
    Square pad an SITK image.

    This means that all image dimension have the same size.

    Parameters
    ----------
    sitk_img: sitk.Image
        the image to be padded
    pad_value: float
        the constant value used for padding

    Returns
    -------
    sitk.Image
    """
    max_size = max(sitk_img.GetSize())

    padding_lower = []
    padding_upper = []
    for s in sitk_img.GetSize():
        padding_lower.append(math.ceil((max_size - s) / 2))
        padding_upper.append(math.floor((max_size - s) / 2))

    return sitk.ConstantPad(
        sitk_img, tuple(padding_lower), tuple(padding_upper), pad_value
    )


def normalize_image(img: np.array, clip: Optional[float] = None) -> np.array:
    """
    Normalize an image and convert its type to `np.uint8` for display.

    Parameters
    ----------
    img: np.array
        the image to be normalized
    clip: optional float
        clip the maximum value in the image to this value before normalization

    Returns
    -------
    np.array
    """
    if img.max() - img.min() == 0.0:
        return np.zeros(img.shape, np.uint8)

    img = np.clip(img, a_min=img.min(), a_max=clip)
    img = (img - img.min()) / (img.max() - img.min())
    img = (255 * img).astype(np.uint8)
    return img

