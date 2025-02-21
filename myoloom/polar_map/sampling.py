import numpy as np
from numpy.typing import NDArray


def polar_grid(
    image: NDArray,
    radii: NDArray,
    azimuth_angles: NDArray,
    polar_angles: NDArray,
    center_z: int = None,
    n_septal: int = None,
    n_lateral: int = None,
) -> tuple[NDArray, NDArray, NDArray]:
    """
    Create a polar sampling grid.

    Actually, this is not only sampling in polar coordinates but also
    in spherical coordinates. It is a preprocessing step to compute
    polar maps from an image of the myocard. The resulting sampling grid
    can be used to resample:
    `scipy.ndimage.map_coordinates(image, polar_grid(image, ...))`
    The resampled image can be used to sample the maximum activity
    per slice and azimuth angle, which forms the basis of drawing
    a polar map.

    Parameters
    ----------
    image: NDArray
        the image (in short-axis view) for which polar sampling
        grid is created
    radii: NDArray
        1D array of radii in image space - range=[0, image.shape[1] / 2)
    azimuth_angles: NDArray
        1D array of azimuth_angles in radians - range=[0, 2*pi)
    polar_angles: NDArray
        1D array of polar angles in radians - range=[0, 0.5*pi)
        polar angles are defined as the angle between x-y-plane and point,
        not between z-axis and point
    center_z: int, default is image.shape[0] // 2
        image[:center_z] will be sampled in spherical coordinates (apex)
        image[center_z:] each slice will be sampled in polar coordinates (cylindrical domain)

    Result
    ------
    tuple of NDArray
        z, y, x coordinates used for resampling the image in polar coordinates
        each coordinate array has the following shape:
        (len(polar_angles) + image.shape[0] - center_z, len(radii), len(azimuth_angles))
    """
    # retrieve center
    _center_z, center_y, center_x = np.array(image.shape) // 2
    center_z = center_z if center_z is not None else _center_z

    # Note: we subtract 0.5 * pi so that sampling 12:00 instead of 3:00
    azimuth_angles = np.mod(azimuth_angles - np.deg2rad(90), np.deg2rad(360))

    n_lateral = image.shape[0] - center_z if n_lateral is None else n_lateral
    n_septal = n_lateral if n_septal is None else n_septal

    # compute result grid shape
    grid_shape = (
        len(polar_angles) + n_lateral,
        len(radii),
        len(azimuth_angles),
    )

    # initialize grid for each coordinate
    grid_x = np.zeros(grid_shape, np.float32)
    grid_y = np.zeros(grid_shape, np.float32)
    grid_z = np.zeros(grid_shape, np.float32)

    # initialize x- and y-grid with polar sampling
    polar_grid_x = np.outer(radii, np.cos(azimuth_angles))
    polar_grid_y = np.outer(radii, np.sin(azimuth_angles))

    # initialize spherical part of z-grid
    grid_z[: len(polar_angles)] = np.repeat(
        (center_z - np.outer(np.cos(polar_angles), radii))[:, :, np.newaxis],
        len(azimuth_angles),
        axis=2,
    )
    # update spherical part of x- and y-grid
    for k, polar_angle in enumerate(polar_angles):
        grid_x[k] = center_x + (polar_grid_x * np.sin(polar_angle))
        grid_y[k] = center_y + (polar_grid_y * np.sin(polar_angle))

    # TODO: comment/describe
    w_min = (n_septal - 1) / (n_lateral - 1)
    w_max = 1.0
    z_weights = np.abs(np.deg2rad(180) - azimuth_angles) / np.deg2rad(180)
    z_weights = z_weights * (w_max - w_min) + w_min

    # update cylindrical part of x- and y-grid
    for k in range(len(polar_angles), grid_shape[0]):
        grid_x[k] = center_x + polar_grid_x
        grid_y[k] = center_y + polar_grid_y
        # in cylindrical domain, the z grid just points to the slice
        grid_z[k] = center_z + (k - len(polar_angles)) * z_weights

    return (grid_z, grid_y, grid_x)


def cartesian_grid(
    polar_image: NDArray, n_samples: int = 256
) -> tuple[NDArray, NDArray]:
    """
    Create a sampling grid to resample an image from polar coordinates in cartesian coordinates.

    After resampling in image with `polar_grid` and selecting the maximum activity per
    azimuth (e.g., just selecting the maximum by radii), this method resamples the
    maximum activity into a polar map image.

    Parameters
    ----------
    polar_image: np.NDArray
        An image in polar coordinates. It is assumed that the first axes corresponds
        to the radius and the second to the azimuth angle.
    n_samples: int
        number of samples in x and y direction

    Returns
    -------
    tuple of NDArray
        y, x coordinates used for resampling the image in cartesian coordinates
        their shape is (n_samples, n_samples)
    """
    max_radius = polar_image.shape[0] - 1
    max_angle = polar_image.shape[1] - 1

    center = (n_samples - 1) / 2
    samples = np.arange(n_samples)
    ys, xs = np.meshgrid(samples, samples)
    ys = ys - center
    xs = xs - center

    radii = np.sqrt(xs**2 + ys**2)
    grid_y = max_radius * radii / center  # normalize to input image range

    angles = -np.arctan2(ys, xs)
    angles = np.pi + angles  # move from [-pi, pi] to [0, 2*pi]
    # angles = np.mod(angles - 0.5 * np.pi, 2.0 * np.pi)
    grid_x = max_angle * angles / (2.0 * np.pi)  # normalize to input image range

    return (grid_y, grid_x)
