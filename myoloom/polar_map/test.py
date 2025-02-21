from dataclasses import dataclass

from reacTk.state import PointState
from reacTk.widget.canvas.image import Image
from reacTk.widget.canvas.line import Line, LineData, LineState, LineStyle
from reacTk.widget.canvas.text import Text, TextData, TextState, TextStyle
from widget_state import NumberState, ListState


@dataclass
class LocationLabel:
    left: str
    right: str
    top: str
    bottom: str


LABELS_SA = LocationLabel(
    left="Septal", right="Lateral", top="Inferior", bottom="Anterior"
)
LABELS_HLA = LocationLabel(left="Septal", right="Lateral", top="Apex", bottom="Basis")
LABELS_VLA = LocationLabel(
    left="Basis", right="Apex", top="Anterior", bottom="Inferior"
)

DEFAULT_LINE_STYLE = LineStyle(
    color="green",
    width=1,
    dash=ListState([NumberState(5), NumberState(5)]),
)
DEFAULT_TEXT_STYLE = TextStyle(
    color="white",
    font_size=12,
)


def label_locations(
    image: Image,
    label: LocationLabel,
    line_style: LineStyle = None,
    text_style=None,
    text_offset: NumberState = None,
):
    line_style = line_style if line_style is not None else DEFAULT_LINE_STYLE
    text_style = text_style if text_style is not None else DEFAULT_TEXT_STYLE
    text_offset = text_offset if text_offset is not None else text_style.font_size

    width = image.data.width()
    height = image.data.height()
    width_half = width // NumberState(2)
    height_half = height // NumberState(2)

    left = image.point_to_canvas(PointState(0, height_half))
    right = image.point_to_canvas(PointState(width, height_half))
    line_horizontal = Line(image.canvas, LineState(LineData(left, right), line_style))

    top = image.point_to_canvas(PointState(width_half, 0))
    bottom = image.point_to_canvas(PointState(width_half, height))
    line_vertical = Line(image.canvas, LineState(LineData(top, bottom), line_style))

    style_text_left = TextStyle(color=text_style.color, font_size=text_style.font_size)
    style_text_left.angle.value = 90
    text_left = Text(
        image.canvas,
        TextState(
            data=TextData(text=label.left, position=left + PointState(text_offset, 0)),
            style=style_text_left,
        ),
    )

    style_text_right = TextStyle(color=text_style.color, font_size=text_style.font_size)
    style_text_right.angle.value = 270
    text_right = Text(
        image.canvas,
        TextState(
            data=TextData(
                text=label.right, position=right - PointState(text_offset, 0)
            ),
            style=style_text_right,
        ),
    )

    text_top = Text(
        image.canvas,
        TextState(
            data=TextData(text=label.top, position=top + PointState(0, text_offset)),
            style=text_style,
        ),
    )
    text_bottom = Text(
        image.canvas,
        TextState(
            data=TextData(
                text=label.bottom, position=bottom - PointState(0, text_offset)
            ),
            style=text_style,
        ),
    )
