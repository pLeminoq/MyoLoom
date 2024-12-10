from .lib import IntState, SequenceState


class PointState(SequenceState):
    """
    Point state that represents 2D pixel coordinates.

    It is often used for drawing.
    """

    def __init__(self, x: IntState, y: IntState):
        super().__init__(values=[x, y], labels=["x", "y"])
