from .lib import SequenceState, IntState


class ResolutionState(SequenceState):

    def __init__(self, width: IntState, height: IntState):
        """
        State defining the resolution of a displayed image.
        """
        super().__init__(values=[width, height], labels=["width", "height"])
