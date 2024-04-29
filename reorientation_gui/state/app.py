from typing import Tuple

print("B")
from reorientation_gui.state.lib import State, StringState
from reorientation_gui.state.reorientation import ReorientationState


class AppState(State):

    def __init__(
        self,
        filename_image = StringState,
        filename_mumap = StringState,
        # reorientation: ReorientationState,
        # canvas_resolution: Tuple[int, int] = (512, 512),
    ):
        print("A")
        super().__init__()

        # self.reorientation = reorientation
        # self.canvas_resolution = (512, 512)

        self.filename_image = filename_image
        self.filename_mumap = filename_mumap
        print("C")

        self.filename_image.on_change(lambda state: print(f"Image filename is {state.value}"))
        self.filename_mumap.on_change(lambda state: print(f"MuMap filename is {state.value}"))

    
