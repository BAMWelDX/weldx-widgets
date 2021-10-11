"""Tests for groove selection widget."""
import weldx
from weldx_widgets import WidgetGrooveSelectionTCPMovement


def setup_module(module):
    """Set Agg matplotlib backend for this module."""
    import matplotlib

    matplotlib.use("Agg", force=True)


def test_groove_linear_sel_tcp_movement_export():
    """Test export."""
    w = WidgetGrooveSelectionTCPMovement()
    tree = w.to_tree()
    # dump
    weldx.WeldxFile(tree=tree, mode="rw")
