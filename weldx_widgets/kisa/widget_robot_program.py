"""Widget to create a robot program."""
import base64
import hashlib
import tempfile
from io import BytesIO
from pathlib import Path
from typing import Callable, Optional, Union

import ipywidgets as widgets
import numpy as np
import pint
from ipywidgets import HTML, Button, Label, Layout

from weldx import Q_, WeldxFile
from weldx.tags.core.file import ExternalFile
from weldx_widgets.widget_base import WidgetMyVBox
from weldx_widgets.widget_factory import FloatWithUnit, make_title

__all__ = [
    "WidgetLinearWeldYaskawa",
]


def download_button(
    content: bytes,
    filename: str,
    button_description: str,
    html_instance: Optional[HTML] = None,
) -> HTML:
    """Load data from buffer into base64 payload embedded into a HTML button.

    Parameters
    ----------
    content :
        file contents as bytes.
    filename :
        The name when it is downloaded.
    button_description :
        The text that goes into the button.
    html_instance :
        update a passed instance or create a new one.
    """
    digest = hashlib.md5(content).hexdigest()  # bypass browser cache
    payload = base64.b64encode(content).decode()
    id_dl = f"dl_{digest}"
    html_button = f"""<html>
    <head>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    </head>
    <body>
    <a id={id_dl} download="{filename}" href="data:text/text;base64,{payload}" >
    <button class="p-Widget jupyter-widgets jupyter-button widget-button mod-success">
    {button_description}</button>
    </a>
    </body>
    </html>
    """
    if html_instance is None:
        html_instance = HTML()

    html_instance.value = html_button
    return html_instance


class WidgetLinearWeldYaskawa(WidgetMyVBox):
    """After process parameters and groove shape selection, generate a program.

    The program is created with one button, then downloaded with another.
    Another side-effect of saving this widget into a weldx file is, that the content
    of the robot program is stored in the weldx file.

    Parameters
    ----------
    wx_file :
        Weldx input file name, has to contain geometry and welding seam information.
    program_func :
        Callable to create to actual robot program.
    """

    def __init__(
        self,
        wx_file: str,
        program_func: Callable[
            [Union[str, Path, WeldxFile], pint.Quantity, str, bool], Union[Path, bytes]
        ],
    ):
        self.wx_file = wx_file
        self.program_func = program_func
        # The translation from the user frame (UF) to the
        # workpiece coordinate system (WCS).
        # The vector points UF -> WCS.
        xyz = (
            FloatWithUnit(text="x", unit="mm", value=-20, min=-999999),
            FloatWithUnit(text="y", unit="mm", value=115.8, min=-999999),
            FloatWithUnit(text="z [optional]", unit="mm", value=0, min=-999999),
        )

        self.uf_to_workpiece = WidgetMyVBox(
            children=[
                Label(
                    "Translation vector from user frame to workpiece coordinate system",
                ),
                *xyz,
            ]
        )
        self.jobname = widgets.Text(description="Jobname", value="MAIN_LINEAR_NEW")

        self.button_create = Button(
            description="Create program",
        )
        self.button_create.on_click(self.create_linear_program)

        # changes to x, y, z or job name invalidate the download button
        for elem in xyz:
            for w in elem.children[1:]:
                w.observe(self._invalidate_dl_button)
        self.jobname.observe(self._invalidate_dl_button)

        super(WidgetLinearWeldYaskawa, self).__init__(
            children=[
                make_title("Create Yaskawa program (linear seam)"),
                self.uf_to_workpiece,
                self.jobname,
                self.button_create,
                HTML(),
            ],
            layout=Layout(width="500px"),
        )

    def _invalidate_dl_button(self, _):
        self.children[-1].value = ""

    def create_linear_program(self, _):
        """Invoke self.program_func with form parameters and create download button."""
        base_unit = self.uf_to_workpiece.children[1].unit
        uf_to_workpiece = Q_(np.array([None, None, None]), base_unit)
        uf_to_workpiece[0] = self.uf_to_workpiece.children[1].quantity.to(base_unit)
        uf_to_workpiece[1] = self.uf_to_workpiece.children[2].quantity.to(base_unit)
        if self.uf_to_workpiece.children[3].float_value != 0:
            uf_to_workpiece[2] = self.uf_to_workpiece.children[3].quantity.to(base_unit)
        else:
            uf_to_workpiece = uf_to_workpiece[:2]
            assert len(uf_to_workpiece) == 2

        with WeldxFile(self.wx_file, mode="r") as wx_input:
            temp: BytesIO = wx_input.write_to(None)
        output: bytes = self.program_func(temp, uf_to_workpiece, write_file=False)
        dl_button = self.children[-1]
        download_button(
            output,
            filename=f"{self.jobname.value}.JBI",
            button_description="Download program",
            html_instance=dl_button,
        )

    def to_tree(self) -> dict:
        """Export state."""
        fn = Path(self.jobname.value)
        temp_dir = tempfile.TemporaryDirectory()
        with open(temp_dir.name / fn) as fh:
            fh.write(self.output)
            external_file = ExternalFile(fh.name, asdf_save_content=True)
            return dict(robot_program=external_file)

    def from_tree(self, tree):
        """Set state. Is currently a dummy."""
