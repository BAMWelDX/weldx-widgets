import pytest

import weldx
from weldx_widgets import WidgetGMAW


def test_to_tree():
    """Ensure exporting works."""
    w = WidgetGMAW()
    weldx.WeldxFile(tree=w.to_tree(), mode="rw")


def test_from_tree():
    """Ensure reading in works."""
    w = WidgetGMAW()
    wx = weldx.WeldxFile(tree=w.to_tree(), mode="rw")
    w.from_tree(wx.data)


@pytest.mark.parametrize(("kind", "write_file"),
                         (("spray", True),
                          ("UI", True),
                          ("II", True),
                         ))
def test(kind, write_file):
    w = WidgetGMAW(process_type=kind)
    tree = w.to_tree()

    # TODO: manipulate widget to contain some non-default values!

    if write_file:
        tree = {key: value for key, value in weldx.WeldxFile(tree=tree, mode="rw").items()
                if key not in ("asdf_library", "history")
                }

    w2 = WidgetGMAW()

    w2.from_tree(tree)

    assert w2.to_tree() == tree