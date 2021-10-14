"""Tests for save widget."""
import weldx
from weldx_widgets.kisa.save import SaveAndNext


def test_on_save(tmpdir):
    """Ensure data from input widget get serialized to desired output file."""

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

    out_file = str(tmpdir / "out")
    status = "test"
    w = SaveAndNext(
        out_file, next_notebook="no", collect_data_from=[SimpleIO()], status=status
    )
    w.on_save(None)
    # verify output
    with weldx.WeldxFile(out_file) as wx:
        assert wx["data"] == 42
        assert wx["wx_user"]["KISA"]["status"] == status
