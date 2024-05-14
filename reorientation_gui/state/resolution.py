from reorientation_gui.state.lib import SequenceState, IntState


class ResolutionState(SequenceState):

    def __init__(self, width: IntState, height: IntState):
        super().__init__(values=[width, height], labels=["width", "height"])
