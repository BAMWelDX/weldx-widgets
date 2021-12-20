"""Tests for WidgetShieldingGas."""
import pytest

from weldx import WeldxFile
from weldx_widgets import WidgetShieldingGas
from weldx_widgets.tests.util import voila_language
from weldx_widgets.widget_gas import WidgetSimpleGasSelection


@pytest.mark.parametrize("write_file", (True, False))
def test_import_export(write_file):
    """Test IO."""
    w = WidgetShieldingGas()
    # simulate adding a gas
    w.gas_components.gas_selection.index = 3
    w.gas_components._add_gas_comp(None)
    percentages = (80, 20)
    for i, (name, box) in enumerate(w.gas_components.components.items()):
        box.children[1].value = percentages[i]
    tree = w.to_tree()
    if write_file:
        tree = {
            key: value
            for key, value in WeldxFile(tree=tree, mode="rw").items()
            if key not in ("history", "extensions", "asdf_library")
        }

    w2 = WidgetShieldingGas()
    w2.from_tree(tree)
    assert w2.to_tree() == tree


def test_lang():
    """Test translation."""
    with voila_language(lang="de"):
        w = WidgetSimpleGasSelection()
    assert "Sauerstoff" in w.gas_list
