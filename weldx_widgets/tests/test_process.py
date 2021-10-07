"""Tests for GMAW widgets."""
import pytest

import weldx
from weldx_widgets import WidgetGMAW


@pytest.mark.parametrize(
    ("kind", "write_file"),
    (
        ("spray", True),
        ("UI", True),
        ("II", True),
    ),
)
def test_import_export(kind, write_file):
    """Ensure import and exports of Widgets works."""
    w = WidgetGMAW(process_type=kind)
    tree = w.to_tree()

    # TODO: manipulate widget to contain some non-default values!

    if write_file:
        tree = {
            key: value
            for key, value in weldx.WeldxFile(tree=tree, mode="rw").items()
            if key not in ("asdf_library", "history")
        }

    w2 = WidgetGMAW()
    w2.from_tree(tree)

    assert w2.to_tree() == tree
