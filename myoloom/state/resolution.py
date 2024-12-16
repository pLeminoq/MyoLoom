from widget_state import DictState, IntState


class ResolutionState(DictState):

    def __init__(self, width: IntState, height: IntState):
        """
        State defining the resolution of a displayed image.
        """
        super().__init__()

        self.width = width
        self.height = height
