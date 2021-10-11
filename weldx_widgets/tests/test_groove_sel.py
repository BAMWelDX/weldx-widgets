"""Tests for groove selection widget."""
import pytest

import weldx
from weldx.welding.groove.iso_9692_1 import _create_test_grooves
from weldx_widgets import WidgetGrooveSelection, WidgetGrooveSelectionTCPMovement

test_grooves = _create_test_grooves()
# ff_grooves = {k,v for k,v in test_grooves if k.startswith("ff_groove")}


def setup_module(module):
    """Set Agg matplotlib backend for this module."""
    import matplotlib

    matplotlib.use("Agg", force=True)


@pytest.mark.parametrize("groove_name", test_grooves.keys())
def test_groove_sel(groove_name):
    """Check form restoration from test grooves."""
    w = WidgetGrooveSelection()
    w.groove_obj = test_grooves[groove_name][0]
    tree = w.to_tree()

    w2 = WidgetGrooveSelection()
    w2.from_tree(tree)
    tree2 = w2.to_tree()
    assert tree2 == tree


def test_groove_linear_sel_tcp_movement_export():
    """Test export."""
    w = WidgetGrooveSelectionTCPMovement()
    tree = w.to_tree()
    # dump
    weldx.WeldxFile(tree=tree, mode="rw")
