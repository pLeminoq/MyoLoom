from reorientation_gui.state.lib import IntState, SequenceState

class PointState(SequenceState):

    def __init__(self, x: IntState, y: IntState):
        super().__init__(values=[x, y], labels=["x", "y"])
