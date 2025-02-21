"""
Utility functions that mainly are about image operations.
"""

import math
from typing import Optional, Tuple

import numpy as np
from PIL import Image, ImageTk
import pydicom
import SimpleITK as sitk


def change_spacing(
    sitk_img: sitk.Image,
    target_spacing: Tuple[float, float, float],
    target_shape: Optional[Tuple[int, int, int]] = None,
) -> sitk.Image:
    """
    Change the spacing and size of an SITK image.

    Parameters
    ----------
    img: sitk.Image
        The image of which the spacing and size is changed.
    target_spacing: tuple of float
        The new spacing.
    target_shape: tuple of int, optional
        The new size which is computed from the old spacing and size
        if not provided.

    Returns
    -------
    sitk.Image
    """
    source_shape = np.array(sitk_img.GetSize())
    source_spacing = np.array(sitk_img.GetSpacing())

    target_spacing = np.array(target_spacing)
    target_spacing = np.where(target_spacing < 0, source_spacing, target_spacing)

    if target_shape is None:
        target_shape = (source_shape * source_spacing) / np.array(target_spacing)
        target_shape = tuple(map(round, target_shape))

    return sitk.Resample(
        sitk_img,
        target_shape,
        sitk.Transform(),
        sitk.sitkLinear,
        sitk_img.GetOrigin(),
        target_spacing,
        sitk_img.GetDirection(),
    )


def center_crop(sitk_img: sitk.Image, target_shape: Tuple[int, int, int]) -> sitk.Image:
    """
    Center crop an SITK image to a target shape.

    Note: channel order in the target shape corresponds to numpy channel
    order and channels with negative target values will not be cropped.

    Parameters
    ----------
    sitk_img: sitk.Image
    target_shape: tuple of int

    Returns
    -------
    sitk.Image
    """
    source_shape = np.array(sitk_img.GetSize())
    target_shape = np.array(target_shape)[
        ::-1
    ]  # channel order is inverted between sitk images and numpy arrays
    target_shape = np.where(target_shape < 0, source_shape, target_shape)

    diff_h = (source_shape - target_shape) / 2
    diff_h = np.where(diff_h < 0, 0, diff_h)

    lowerCrop = np.ceil(diff_h).astype(int).tolist()
    upperCrop = np.floor(diff_h).astype(int).tolist()

    return sitk.Crop(sitk_img, lowerCrop, upperCrop)


def center_pad(
    sitk_img: sitk.Image, target_shape: Tuple[int, int, int], value: float = 0
) -> sitk.Image:
    """
    Center pad an SITK image to a target shape.

    Note: channel order in the target shape corresponds to numpy channel
    order and channels with negative target values will not be padded.

    Parameters
    ----------
    sitk_img: sitk.Image
    target_shape: tuple of int
    value: float

    Returns
    -------
    sitk.Image
    """
    source_shape = np.array(sitk_img.GetSize())
    target_shape = np.array(target_shape)[
        ::-1
    ]  # channel order is reverted between sitk images and numpy arrays
    target_shape = np.where(target_shape < 0, source_shape, target_shape)

    diff_h = (target_shape - source_shape) / 2
    diff_h = np.where(diff_h < 0, 0, diff_h)

    lowerPad = np.ceil(diff_h).astype(int).tolist()
    upperPad = np.floor(diff_h).astype(int).tolist()

    return sitk.ConstantPad(sitk_img, lowerPad, upperPad, value)


def pad_crop(
    sitk_img: sitk.Image, target_shape: Tuple[int, int, int], value: float = 0
) -> sitk.Image:
    """
    First `center_pad` and then `center_crop` a SITK image to a target
    shape.

    Note: channel order in the target shape corresponds to numpy channel
    order and channels with negative target values will not be padded.

    Parameters
    ----------
    sitk_img: sitk.Image
    target_shape: tuple of int
    value: float
        value used for padding

    returns
    -------
    sitk.Image
    """
    return center_crop(center_pad(sitk_img, target_shape, value), target_shape)


def resample(
    sitk_img: sitk.Image,
    sitk_img_target: sitk.Image,
    interpolator: int = sitk.sitkLinear,
) -> sitk.Image:
    """
    Re-sample an image so that its spacing, origin, direction ans size match a target image.

    Parameters
    ----------
    sitk_img: sitk.Image
        image to be re-sampled
    sitk_img_target: sitk.Image
        the target image
    interpolator: int, optional
        the type of interpolation used for re-sampling, e.g. sitk.sitkLinear

    Returns
    -------
    sitk.Image
    """
    return sitk.Resample(
        nrrd.header, nrrd_target.header, sitk.Transform(), interpolator
    )


def get_empty_image(
    size: Tuple[int, int, int] = (96, 96, 96),
    spacing: Tuple[float, float, float] = (4.0, 4.0, 4.0),
) -> sitk.Image:
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
    sitk_img = sitk.Image(size, sitk.sitkFloat64)
    sitk_img.SetSpacing(spacing)
    return sitk_img


def load_image(filename: str, target_range: float = 300) -> sitk.Image:
    """
    Load an SITK image from a filename.

    This operations
      * casts the image as float,
      * ensures that the stacking direction of slices is positive,
      * and applies a custom scaling used by Siemens SPECT devices


    Parameters
    ----------
    filename: str
    target_range: float
        the space in mm the image should have in each dimension
        default is 300mm as it is expected to find the heart within half this range
        in the body

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
    except RuntimeError:
        pass

    try:
        """
        Rescale if the header contains the privat tag "PixelScaleFactor=0x00331038".
        """
        scale = float(_sitk_img.GetMetaData("0033|1038"))
        sitk_img = 1.0 * sitk_img / scale
    except RuntimeError:
        pass

    try:
        """
        This is a workaround for the GE Discovery NM530c. It produces DICOM images
        that contain a value for `Slice Thickness` as well as `Spacing Between Slices`
        and they are not the same.
        In these cases the spacing is twice the thickness, which is wrong, but it is
        used by SimpleITK. This code ensures that the thickness will be used instead.
        """
        _ = _sitk_img.GetMetaData(
            "0018|0088"
        )  # test if `SpacingBetweenSlices` is available
        slice_thickness = float(_sitk_img.GetMetaData("0018|0050"))

        sitk_img.SetSpacing((*sitk_img.GetSpacing()[:2], slice_thickness))
    except RuntimeError as e:
        pass

    sitk_img = square_pad(sitk_img)

    target_shape = round(target_range / sitk_img.GetSpacing()[0])
    target_shape = (target_shape,) * 3
    sitk_img = pad_crop(sitk_img, target_shape=target_shape)

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


def is_short_axis(filename: str) -> bool:
    dcm = pydicom.dcmread(filename, stop_before_pixels=True)
    view_code = dcm.DetectorInformationSequence[0].ViewCodeSequence[0]
    return (
        view_code.CodingSchemeDesignator == "SNM3" and view_code.CodeValue == "G-A186"
    )
