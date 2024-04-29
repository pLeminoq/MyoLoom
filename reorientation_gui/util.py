from typing import Optional, Tuple

import cv2 as cv
import numpy as np
from PIL import Image, ImageTk
import SimpleITK as sitk

def visualize_recon_slice(recon: sitk.Image, slice: int, clip_percentage: float = 1.0, color_map: int = cv.COLORMAP_INFERNO, resolution: Tuple[int, int] = (512, 512)) -> np.array:
    img = sitk.GetArrayFromImage(recon)
    img = np.clip(img, a_min=img.min(), a_max=img.max() * clip_percentage)

    if img.max() - img.min() != 0:
        img = (img - img.min()) / (img.max() - img.min())
    else:
        img = img - img.min()
    img = (255 * img).astype(np.uint8)

    img = img[slice]
    img = cv.resize(img, resolution)
    img = cv.applyColorMap(img, color_map)
    img = cv.cvtColor(img, cv.COLOR_BGR2RGB)
    return img

def visualize_mumap_slice(mu_map: sitk.Image, slice: int, max_val: float = 2.0, resolution: Tuple[int, int] = (512, 512)) -> np.array:
    img = sitk.GetArrayFromImage(mu_map)
    img = img / 10000
    img = np.clip(img, a_min=0.0, a_max=max_val)
    img = img / max_val
    img = (255 * img).astype(np.uint8)

    img = img[slice]
    img = cv.resize(img, resolution)
    img = cv.cvtColor(img, cv.COLOR_GRAY2RGB)
    return img

def visualize_slice(recon: sitk.Image, mu_map: sitk.Image, slice: int, resolution: Tuple[int, int], recon_clip_percentage: float = 1.0, recon_color_map: int = cv.COLORMAP_INFERNO, mu_map_max_val: float = 2.0) -> ImageTk:
    slice_recon = visualize_recon_slice(recon, slice, resolution=resolution, clip_percentage=recon_clip_percentage, color_map=recon_color_map)
    slice_mumap = visualize_mumap_slice(mu_map, slice, resolution=resolution, max_val=mu_map_max_val)
    print(slice_mumap.max())

    slice_img = cv.addWeighted(slice_mumap, 0.8, slice_recon, 0.8, 0.0)
    return img_to_tk(slice_img)


def img_to_tk(img: np.array) -> ImageTk:
    return ImageTk.PhotoImage(Image.fromarray(img))

def sitk_to_tk(
    sitk_image: sitk.Image,
    slice: int,
    resolution: Tuple[int, int] = (512, 512),
    max_percent: float = 1.0,
    color_map: Optional[int] = None,
):
    """
    Convert a 3D sitk.Image to an ImageTk for visualization.

    Parameters
    ----------
    sitk_image: sitk.Image
        the image to convert
    slice: int
        the slice of the 3D image to select
    resolution: tuple of int
        the target resolution of the resulting image
    max_percent: float
        clip the image to this percentage of its maximum value
    color_map: int
        optional color map to apply to the image

    Returns
    -------
    ImageTk
    """
    img = sitk.GetArrayFromImage(sitk_image)

    img = np.clip(img, a_min=img.min(), a_max=img.max() * max_percent)
    if img.max() - img.min() != 0:
        img = (img - img.min()) / (img.max() - img.min())
    else:
        img = img - img.min()
    img = (255 * img).astype(np.uint8)

    img = img[slice]
    img = cv.resize(img, resolution)
    if color_map is not None:
        img = cv.applyColorMap(img, color_map)
        img = cv.cvtColor(img, cv.COLOR_BGR2RGB)

    return ImageTk.PhotoImage(Image.fromarray(img))
