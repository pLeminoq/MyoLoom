import numpy as np

from reorientation_gui.state.lib import State

class ImageState(State):

    def __init__(self, image: np.array):
        super().__init__(verify_change=False)

        self.image = image

    def update(self, image: np.array):
        self.image = image
        self.notify_change()


