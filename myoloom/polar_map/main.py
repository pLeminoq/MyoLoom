import tkinter as tk
from tkinter import ttk

import cv2 as cv
import numpy as np
from reacTk.widget.canvas.line import Line, LineData, LineState, LineStyle
from reacTk.widget.canvas.image import Image, ImageData, ImageState, ImageStyle
from reacTk.widget.canvas.text import Text, TextData, TextState, TextStyle
from reacTk.widget.canvas import Canvas, CanvasState
from reacTk.state import PointState
from widget_state import compute, ListState, StringState

from .config_view import ConfigView
from .polar_map import PolarMap, polar_map_state
from .state import AppState
from .segment import SEGMENTS, segment_mask, segment_center
from ..widget.slice_view import SliceView, SliceViewState


class App(ttk.Frame):
    def __init__(self, parent: tk.Widget, state: AppState):
        super().__init__()

        self.state = state
        self.state.radial_activities.on_change(lambda s: polar_map_state.radial_activities.set(s.value))

        self.config_view = ConfigView(self, state.config_view_state)
        self.config_view.grid(row=0, column=0, sticky="nswe")

        self.polar_map = PolarMap(self, polar_map_state)
        self.polar_map.grid(row=0, column=1, sticky="nswe")

        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=3)
        self.rowconfigure(0, weight=1)
