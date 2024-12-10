from typing import Optional, List, Tuple
import time

import numpy as np
import SimpleITK as sitk

from .lib import SequenceState, HigherState, FloatState, IntState


class AngleState(SequenceState):

    def __init__(self, x: FloatState = 0.0, y: FloatState = 0.0, z: FloatState = 0.0):
        """
        State defining a rotation around the three axes.
        """
        super().__init__(values=[x, y, z], labels=["x", "y", "z"])


class CenterState(SequenceState):

    def __init__(self, x: IntState, y: IntState, z: IntState):
        """
        State defining a 3D translation.
        """
        super().__init__(values=[x, y, z], labels=["x", "y", "z"])


class ReorientationState(HigherState):
    """
    State keeping track of the reorientation (rotation and translation) parameters.
    """

    def __init__(self, angle_state: AngleState, center_state: CenterState):
        super().__init__()

        self.angle_state = angle_state
        self.center_state = center_state
