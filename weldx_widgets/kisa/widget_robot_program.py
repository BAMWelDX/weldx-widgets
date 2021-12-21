"""Widget to create a robot program."""
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
from weldx_widgets.generic import download_button
from weldx_widgets.translation_utils import _i18n as _
from weldx_widgets.widget_base import WidgetMyVBox
from weldx_widgets.widget_factory import FloatWithUnit, make_title

__all__ = [
    "WidgetLinearWeldYaskawa",
]


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
        self.temp_dir = tempfile.TemporaryDirectory()  # outputs will be stored here.
        self.output: Optional[bytes] = None  # binary contents of robot program.
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
        self.jobname = widgets.Text(description=_("Jobname"), value="MAIN_LINEAR_NEW")

        self.button_create = Button(
            description=_("Create program"),
        )
        self.button_create.on_click(self.create_linear_program)

        # changes to x, y, z or job name invalidate the download button
        for elem in xyz:
            for w in elem.children[1:]:
                w.observe(self._invalidate_dl_button)
        self.jobname.observe(self._invalidate_dl_button)

        super(WidgetLinearWeldYaskawa, self).__init__(
            children=[
                make_title(_("Create Yaskawa program (linear seam)")),
                self.uf_to_workpiece,
                self.jobname,
                self.button_create,
                HTML(),
            ],
            layout=Layout(width="500px"),
        )

    def _invalidate_dl_button(self, button):
        self.children[-1].value = ""

    def create_linear_program(self, button):
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
            button_description=_("Download program"),
            html_instance=dl_button,
        )

        self.output = output

    def to_tree(self) -> dict:
        """Export state."""
        if not self.output:
            return {}
        fn = Path(self.jobname.value)
        with open(self.temp_dir.name / fn, mode="wb") as fh:
            fh.write(self.output)
            external_file = ExternalFile(fh.name, asdf_save_content=True)
            return dict(robot_program=external_file)

    def from_tree(self, tree):
        """Set state. Is currently a dummy."""
