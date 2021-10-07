"""Utility functions to set widget state from a given file."""
from typing import Iterable, Union

from widget_base import WeldxImportExport

import weldx
from weldx_widgets.kisa.save import get_param_from_env


def set_state_from_file(
    widget: Union[WeldxImportExport, Iterable[WeldxImportExport]], file=None
):
    """Set the state of given widgets from weldx file tree."""
    if not file:
        file = get_param_from_env("file")

    if not isinstance(widget, Iterable):
        widget = [widget]

    with weldx.WeldxFile(file, mode="r") as wx:
        for w in widget:
            w.from_tree(wx)
