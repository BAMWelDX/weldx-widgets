"""Tests for groove selection widget."""
import pytest

import weldx
from weldx.welding.groove.iso_9692_1 import _create_test_grooves
from weldx_widgets import WidgetGrooveSelection, WidgetGrooveSelectionTCPMovement

test_grooves = _create_test_grooves()


@pytest.mark.parametrize("groove_name", test_grooves.keys())
def test_groove_sel(groove_name):
    """Check form restoration from test grooves."""
    groove_obj = test_grooves[groove_name][0]
    w = WidgetGrooveSelection()
    w.groove_obj = groove_obj
    tree = w.to_tree()
    gui_params = w.groove_params_dropdowns
    if not groove_name.startswith("ff"):  # non ff-grooves
        assert gui_params["workpiece_thickness"].quantity == groove_obj.t
        assert gui_params["root_gap"].quantity == groove_obj.b
        try:
            assert gui_params["root_face"].quantity == groove_obj.c
        except AttributeError:
            pass
        try:
            assert gui_params["groove_angle"].quantity == groove_obj.alpha
        except AttributeError:
            pass
    else:
        assert gui_params["workpiece_thickness"].quantity == groove_obj.t_1

    w2 = WidgetGrooveSelection()
    w2.from_tree(tree)
    tree2 = w2.to_tree()
    assert tree2 == tree


def test_groove_linear_sel_tcp_movement_export():
    """Test export."""
    w = WidgetGrooveSelectionTCPMovement()
    w.create_csm_and_plot()
    w.geometry_export.create_btn.click()  # simulate an geometry export with defaults.
    tree = w.to_tree()
    # dump
    tree = weldx.WeldxFile(tree=tree, mode="rw")
    tree.pop("asdf_library")
    tree.pop("history")

    w2 = WidgetGrooveSelectionTCPMovement()
    w2.from_tree(tree)
    tree2 = w2.to_tree()

    assert tree2 == tree
