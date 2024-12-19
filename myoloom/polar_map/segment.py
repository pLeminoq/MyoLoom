from dataclasses import dataclass
from typing import Optional

import numpy as np
from numpy.typing import NDArray


def polar_2_cartesian(
    radius: float, angle: float, start_angle: float = -np.deg2rad(90)
) -> tuple[float, float]:
    x = radius * np.cos(angle + start_angle)
    y = radius * np.sin(angle + start_angle)
    return x, y


@dataclass
class Segment:
    id: int
    location: str
    name: str
    angle_range: tuple[float, float]
    radius_range: tuple[float, float]


SEGMENTS = [
    # basal segments
    Segment(
        id=1,
        location="basal",
        name="anterior",
        angle_range=tuple(np.deg2rad([330, 30])),
        radius_range=(0.75, 1.0),
    ),
    Segment(
        id=2,
        location="basal",
        name="anteroseptal",
        angle_range=tuple(np.deg2rad([270, 330])),
        radius_range=(0.75, 1.0),
    ),
    Segment(
        id=3,
        location="basal",
        name="inferoseptal",
        angle_range=tuple(np.deg2rad([210, 270])),
        radius_range=(0.75, 1.0),
    ),
    Segment(
        id=4,
        location="basal",
        name="inferior",
        angle_range=tuple(np.deg2rad([150, 210])),
        radius_range=(0.75, 1.0),
    ),
    Segment(
        id=5,
        location="basal",
        name="inferolateral",
        angle_range=tuple(np.deg2rad([90, 150])),
        radius_range=(0.75, 1.0),
    ),
    Segment(
        id=6,
        location="basal",
        name="anteroolateral",
        angle_range=tuple(np.deg2rad([30, 90])),
        radius_range=(0.75, 1.0),
    ),
    # mid-cavity segments
    Segment(
        id=7,
        location="mid",
        name="anterior",
        angle_range=tuple(np.deg2rad([330, 30])),
        radius_range=(0.5, 0.75),
    ),
    Segment(
        id=8,
        location="mid",
        name="anteroseptal",
        angle_range=tuple(np.deg2rad([270, 330])),
        radius_range=(0.5, 0.75),
    ),
    Segment(
        id=9,
        location="mid",
        name="inferoseptal",
        angle_range=tuple(np.deg2rad([210, 270])),
        radius_range=(0.5, 0.75),
    ),
    Segment(
        id=10,
        location="mid",
        name="inferior",
        angle_range=tuple(np.deg2rad([150, 210])),
        radius_range=(0.5, 0.75),
    ),
    Segment(
        id=11,
        location="mid",
        name="inferolateral",
        angle_range=tuple(np.deg2rad([90, 150])),
        radius_range=(0.5, 0.75),
    ),
    Segment(
        id=12,
        location="mid",
        name="anteroolateral",
        angle_range=tuple(np.deg2rad([30, 90])),
        radius_range=(0.5, 0.75),
    ),
    # apical segments
    Segment(
        id=13,
        location="apical",
        name="anterior",
        angle_range=tuple(np.deg2rad([315, 45])),
        radius_range=(0.25, 0.5),
    ),
    Segment(
        id=14,
        location="apical",
        name="septal",
        angle_range=tuple(np.deg2rad([225, 315])),
        radius_range=(0.25, 0.5),
    ),
    Segment(
        id=15,
        location="apical",
        name="inferior",
        angle_range=tuple(np.deg2rad([135, 225])),
        radius_range=(0.25, 0.5),
    ),
    Segment(
        id=16,
        location="apical",
        name="lateral",
        angle_range=tuple(np.deg2rad([45, 135])),
        radius_range=(0.25, 0.5),
    ),
    # apex segment
    Segment(
        id=17,
        location="apex",
        name="apex",
        angle_range=tuple(np.deg2rad([0, 360])),
        radius_range=(0.0, 0.25),
    ),
]


def segment_mask(
    activity,
    segment: Segment,
    angles: Optional[NDArray] = None,
) -> NDArray[bool]:
    angles = (
        angles
        if angles is not None
        else 2 * np.pi * np.arange(activity.shape[1]) / activity.shape[1]
    )

    if segment.angle_range[0] > segment.angle_range[1]:
        angle_mask = np.logical_or(
            angles >= segment.angle_range[0],
            angles < segment.angle_range[1],
        )
    else:
        angle_mask = np.logical_and(
            segment.angle_range[0] <= angles,
            angles < segment.angle_range[1],
        )
    angle_mask = np.repeat(angle_mask[np.newaxis, :], activity.shape[0], axis=0)

    radius_range = tuple(
        map(lambda r: round(r * activity.shape[0]), segment.radius_range)
    )
    radius_mask = np.full(activity.shape, False)
    radius_mask[radius_range[0] : radius_range[1]] = True

    return np.logical_and(angle_mask, radius_mask)


def segment_vertices(segment: Segment, radius: int):
    corners = []
    cx, cy = radius, radius
    for angle in segment.angle_range:
        for _radius in segment.radius_range:
            x, y = polar_2_cartesian(_radius * radius, angle)
            corners.append((round(cx + x), round(cy + y)))
    return corners


def segment_center(segment: Segment, radius: int):
    if segment.id == 17:
        return radius, radius
    corners = []
    if segment.angle_range[0] > segment.angle_range[1]:
        mean_angle = (
            (segment.angle_range[0] - np.deg2rad(360)) + segment.angle_range[1]
        ) / 2.0
    else:
        mean_angle = (segment.angle_range[0] + segment.angle_range[1]) / 2.0
    mean_radius = sum(segment.radius_range) / 2.0

    x, y = polar_2_cartesian(mean_radius * radius, mean_angle)
    return round(radius + x), round(radius + y)
