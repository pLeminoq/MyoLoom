import numpy as np
from numpy.typing import NDArray


def weight_polar_rep(
    polar_rep: NDArray, pixel_size_mm: float, sigma: float = 5.0
) -> NDArray:
    """
    Weight a polar representation of a myocardial perfusion image according to the habilitation:
    'Regionale Quantifizierung myokardialer Funktionsparameter in der Positronen-Emissions-Tomographie' - Jörg van den Hoff, 1998.

    This weighting tries to limit the search space for maximum activities along the radius
    by considering average maximum positions and the activity distribution.
    This way, outliers because of large extra myocardial activity or because of bad perfusion are prevented.

    Parameters
    ----------
    polar_rep: NDArray
        polar representation of an image as achieved by resampling with `myoloom.polar_map.sampling.polar_grid`

    Returns
    -------
    NDArray
        weighted polar representation
    """
    if polar_rep.max() == 0.0:
        return polar_rep

    # TODO: improve readability
    average_by_radius = np.average(polar_rep, axis=2)
    averages = np.average(average_by_radius, axis=1)
    max_vals = np.max(average_by_radius, axis=1)
    max_positions = np.argmax(average_by_radius, axis=1)
    weighted_mean_position = round(np.sum(max_vals * max_positions) / np.sum(max_vals))

    def compute_hwm(slice_idx):
        # bigger-than_half-max
        bt_hm = (average_by_radius[slice_idx] - averages[slice_idx]) > 0.5 * (
            average_by_radius[slice_idx] - averages[slice_idx]
        )

        lpos = hpos = max_positions[slice_idx]
        while lpos > 0 and bt_hm[lpos - 1]:
            lpos -= 1
        while hpos < bt_hm.shape[0] - 1 and bt_hm[hpos + 1]:
            hpos += 1

        return (hpos - lpos) // 2

    hwhm = np.array(
        list(
            map(
                lambda i: compute_hwm(i),
                range(polar_rep.shape[0]),
            )
        )
    )

    # built filter to fix difficult regions for hwhm
    filter_1 = hwhm > np.median(hwhm) + 1.5 * np.std(hwhm)
    filter_2 = max_positions - weighted_mean_position > np.median(hwhm)
    filter_3 = max_positions - weighted_mean_position < -np.median(hwhm)
    filter = np.logical_or(filter_1, np.logical_or(filter_2, filter_3))

    center_positions = np.where(filter, weighted_mean_position, max_positions[:])
    hwhm = np.where(filter, np.median(hwhm), hwhm)

    for slice_idx in range(polar_rep.shape[0]):
        # compute average in 1.5 * hwhm range around center_position
        _range = np.full(polar_rep[slice_idx].shape, False, dtype=bool)
        _min = max(0, round(center_positions[slice_idx] - 1.5 * hwhm[slice_idx]))
        _max = min(
            _range.shape[0],
            round(center_positions[slice_idx] + 1.5 * hwhm[slice_idx]),
        )
        _range[_min:_max] = True
        if not _range.any() or polar_rep[slice_idx][_range].max() == 0.0:
            continue

        _avg = np.average(polar_rep[slice_idx][_range])

        valmean = np.average(max_vals)
        offset = hwhm[slice_idx] * np.sqrt(_avg / valmean)

        mu_min = center_positions[slice_idx] - offset
        mu_max = center_positions[slice_idx] + offset

        _sigma = sigma * pixel_size_mm

        xs = np.arange(polar_rep.shape[1])
        _a = 1.0 / (1.0 + np.exp((mu_min - xs) / _sigma))
        _b = 1.0 / (1.0 + np.exp((xs - mu_max) / _sigma))
        weights = _a + _b - 1

        weights = weights[:, np.newaxis].repeat(polar_rep[slice_idx].shape[1], axis=1)

        polar_rep[slice_idx] = weights * polar_rep[slice_idx]
    return polar_rep
