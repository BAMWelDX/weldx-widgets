"""Tests for save widget."""
import shutil

import pytest

import weldx
from weldx_widgets.kisa.save import SaveAndNext


class SimpleIO:
    """Implements serialization protocol for weldx widgets."""

    def __init__(self):
        self.data = 42

    def to_tree(self):
        """Get data."""
        return {"data": self.data}

    def from_tree(self, tree: dict):  # noqa
        """Set data."""
        self.data = tree["data"]


@pytest.mark.parametrize("change", [False, True])
def test_on_save_update(tmpdir, change):
    """Ensure data from input widget get serialized to desired output file.

    Also ensure existing data is preserved, if not being changed by the update.
    """
    out_file = str(tmpdir / "out")

    with weldx.WeldxFile(out_file, mode="rw") as fh:
        fh["wx_user"] = {"some": "data"}

    status = "test"
    w = SaveAndNext(
        out_file, next_notebook="no", collect_data_from=[SimpleIO()], status=status
    )
    if change:  # fake a change of the initial file choice.
        new_file = out_file + "_2"
        shutil.copy(out_file, new_file)
        setattr(SaveAndNext, "filename", new_file)
        w.on_save(None)
        out_file = new_file
    else:
        w.on_save(None)
    # verify output
    with weldx.WeldxFile(out_file) as wx:
        assert wx["data"] == 42
        assert "some" in wx["wx_user"]
        assert wx["wx_user"]["KISA"]["status"] == status
