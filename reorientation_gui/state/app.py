from typing import Tuple

from reorientation_gui.state.image import FileImageState
from reorientation_gui.state.lib import State
from reorientation_gui.state.reorientation import ReorientationState


class AppState(State):

    def __init__(
        self,
        # reorientation: ReorientationState,
        # canvas_resolution: Tuple[int, int] = (512, 512),
    ):
        super().__init__()

        # self.reorientation = reorientation
        # self.canvas_resolution = (512, 512)

        self.file_image_state_spect = FileImageState()
        self.file_image_state_mu_map = FileImageState()
        self.reorientation_state = ReorientationState(
            angle_x=0.0, angle_y=0.0, angle_z=0.0, center_x=64, center_y=64, center_z=64
        )

        self.file_image_state_spect.on_change(self.reset_reorientation)

    def reset_reorientation(self, file_image_state):
        size = file_image_state.sitk_img_state.value.GetSize()

        self.reorientation_state.angle_x.value = 0.0
        self.reorientation_state.angle_y.value = 0.0
        self.reorientation_state.angle_z.value = 0.0

        self.reorientation_state.center_x.value = size[0] // 2
        self.reorientation_state.center_y.value = size[1] // 2
        self.reorientation_state.center_z.value = size[2] // 2

