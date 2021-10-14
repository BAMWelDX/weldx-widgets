"""Widget to create a robot program."""
import base64
import hashlib
import tempfile
from io import BytesIO
from pathlib import Path
from typing import Callable, Union

import ipywidgets
import ipywidgets as widgets
import numpy as np
import pint
from IPython.display import HTML, display
from ipywidgets import Label, Layout

from weldx import Q_, WeldxFile
from weldx.tags.core.file import ExternalFile
from weldx_widgets.widget_base import WidgetMyVBox
from weldx_widgets.widget_factory import FloatWithUnit, make_title

__all__ = [
    "WidgetLinearWeldYaskawa",
]


# TODO: does not work?!?
class DownloadButton(ipywidgets.Button):
    """Download button with dynamic content.

    The content is generated using a callback when the button is clicked.

    # code from: https://stackoverflow.com/a/68683463/3086470
    """

    def __init__(self, filename: str, contents: Callable[[], bytes], **kwargs):
        super(DownloadButton, self).__init__(**kwargs)
        self.filename = filename
        self.contents = contents
        self.on_click(self.__on_click)

    def __on_click(self, b):
        """Handle click."""
        contents = self.contents()
        b64 = base64.b64encode(contents)
        payload = b64.decode()
        digest = hashlib.md5(contents).hexdigest()  # bypass browser cache
        id = f"dl_{digest}"

        display(
            HTML(
                f"""
<html>
<body>
<a id="{id}" download="{self.filename}" href="data:text/csv;base64,{payload}" download>
</a>

<script>
(function download() {{
document.getElementById('{id}').click();
}})()
</script>

</body>
</html>
"""
            )
        )


class WidgetLinearWeldYaskawa(WidgetMyVBox):
    """After process parameters and groove shape selection, generate a program.

    Parameters
    ----------
    file :
        Weldx input file name, has to contain geometry and welding seam information.
    program_func :
        Callable to create to actual roboter program.
    """

    def __init__(
        self,
        file: str,
        program_func: Callable[
            [Union[str, Path, WeldxFile], pint.Quantity, str, bool], Union[Path, bytes]
        ],
    ):
        self.file = file
        self.program_func = program_func
        self.output = None
        # The translation from the user frame (UF) to the
        # workpiece coordinate system (WCS).
        # The vector points UF -> WCS.
        self.uf_to_workpiece = WidgetMyVBox(
            children=[
                Label(
                    "Translation vector from user frame to workpiece coordinate system",
                    layout=Layout(width="100%"),
                ),
                FloatWithUnit(text="x", unit="mm", value=-20, min=-999999),
                FloatWithUnit(text="y", unit="mm", value=115.8, min=-999999),
                FloatWithUnit(text="z", unit="mm", value=0, min=-999999),
            ]
        )
        self.jobname = widgets.Text(description="Jobname", value="MAIN_LINEAR_NEW")
        self.button = DownloadButton(
            description="Create program",
            contents=self.create_linear_program,
            filename=self.jobname.value + ".JBI",
        )

        super(WidgetLinearWeldYaskawa, self).__init__(
            children=[
                make_title("Create Yaskawa program (linear seam)"),
                self.uf_to_workpiece,
                self.jobname,
                self.button,
            ],
            layout=Layout(width="500px"),
        )

    def create_linear_program(self):
        """Invoke self.program_func with form parameters."""
        base_unit = self.uf_to_workpiece.children[1].unit
        uf_to_workpiece = Q_(np.array([None, None, None]), base_unit)
        uf_to_workpiece[0] = self.uf_to_workpiece.children[1].quantity.to(base_unit)
        uf_to_workpiece[1] = self.uf_to_workpiece.children[2].quantity.to(base_unit)
        if self.uf_to_workpiece.children[3].float_value != 0:
            uf_to_workpiece[2] = self.uf_to_workpiece.children[3].quantity.to(base_unit)
        else:
            uf_to_workpiece = uf_to_workpiece[:2]
            assert len(uf_to_workpiece) == 2

        with WeldxFile(self.file, mode="r") as wx_input:
            temp: BytesIO = wx_input.write_to(None)
            output: bytes = self.program_func(temp, uf_to_workpiece, write_file=False)
            print("output", output)
            self.output = output
            return output

    def to_tree(self) -> dict:
        """Export state."""
        fn = Path(self.jobname.value)
        temp_dir = tempfile.TemporaryDirectory()
        with open(temp_dir.name / fn) as fh:
            fh.write(self.output)
            external_file = ExternalFile(fh.name, asdf_save_content=True)
            return dict(roboter_program=external_file)

    def from_tree(self, tree):
        """Set state. Is currently a dummy."""
        pass
