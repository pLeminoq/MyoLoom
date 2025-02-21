from typing import Optional, List, Tuple
import time

import numpy as np
import SimpleITK as sitk
from widget_state import DictState, NumberState, HigherOrderState


class AngleState(DictState):
    def __init__(
        self,
        x: float | NumberState = 0.0,
        y: float | NumberState = 0.0,
        z: float | NumberState = 0.0,
    ):
        """
        State defining a rotation around the three axes.
        """
        super().__init__()

        self.x = x if isinstance(x, float) else NumberState(x)
        self.y = y if isinstance(y, float) else NumberState(y)
        self.z = z if isinstance(z, float) else NumberState(z)


class CenterState(DictState):
    def __init__(
        self, x: float | NumberState, y: float | NumberState, z: float | NumberState
    ):
        """
        State defining a 3D translation.
        """
        super().__init__()

        self.x = x if isinstance(x, float) else NumberState(x)
        self.y = y if isinstance(y, float) else NumberState(y)
        self.z = z if isinstance(z, float) else NumberState(z)


class ReorientationState(HigherOrderState):
    """
    State keeping track of the reorientation (rotation and translation) parameters.
    """

    def __init__(self, angle: AngleState, center: CenterState):
        super().__init__()

        self.angle = angle
        self.center = center
