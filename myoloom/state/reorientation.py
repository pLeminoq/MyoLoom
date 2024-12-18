from typing import Optional, List, Tuple
import time

import numpy as np
import SimpleITK as sitk
from widget_state import DictState, FloatState, HigherOrderState, IntState


class AngleState(DictState):

    def __init__(
        self,
        x: float | FloatState = 0.0,
        y: float | FloatState = 0.0,
        z: float | FloatState = 0.0,
    ):
        """
        State defining a rotation around the three axes.
        """
        super().__init__()

        self.x = x if isinstance(x, float) else FloatState(x)
        self.y = y if isinstance(y, float) else FloatState(y)
        self.z = z if isinstance(z, float) else FloatState(z)


class CenterState(DictState):

    def __init__(self, x: float | FloatState, y: float | FloatState, z: float | FloatState):
        """
        State defining a 3D translation.
        """
        super().__init__()

        self.x = x if isinstance(x, float) else FloatState(x)
        self.y = y if isinstance(y, float) else FloatState(y)
        self.z = z if isinstance(z, float) else FloatState(z)


class ReorientationState(HigherOrderState):
    """
    State keeping track of the reorientation (rotation and translation) parameters.
    """

    def __init__(self, angle: AngleState, center: CenterState):
        super().__init__()

        self.angle = angle
        self.center = center
