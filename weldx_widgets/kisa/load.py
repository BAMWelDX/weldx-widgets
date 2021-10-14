"""Utility functions to set widget state from a given file."""
from pathlib import Path
from typing import Iterable, Union

import weldx
from weldx_widgets.kisa.save import get_param_from_env
from weldx_widgets.widget_base import WeldxImportExport


def set_state_from_file(
    widget: Union[WeldxImportExport, Iterable[WeldxImportExport]], file=None
):
    """Set the state of given widgets from weldx file tree."""
    if not file:
        file = get_param_from_env("file")

    if not isinstance(widget, Iterable):
        widget = [widget]

    if isinstance(file, (str, Path)):
        file = Path(file)
        if file.exists() and file.stat().st_size > 0:
            try:
                with weldx.WeldxFile(file, mode="r") as wx:
                    for w in widget:
                        try:
                            w.from_tree(wx)
                        except KeyError as ke:
                            print(f"Key not found in given file. Details: {ke}")
                        except Exception as e:
                            print(f"Error during reading {file}: {e}")
            except Exception as e:
                print(f"Error during reading {file}: {e}")
    else:
        print(f"Unknown input file type: {type(file)}")
