"""Tests for GMAW widgets."""
import pytest

import weldx
from weldx import Q_
from weldx_widgets import WidgetGMAW
from weldx_widgets.tests.util import voila_language


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
    proc = w.welding_process
    proc.base_process.manufacturer.text_value = "Quinto"
    proc.base_process.wire_feedrate.quantity = Q_(20, "cm/s")
    # manipulate widget to contain some non-default values!
    if kind == "spray":
        proc.voltage.time_data.text_value = "0, 1"
        proc.impedance.float_value = 230
        proc.characteristic.float_value = 60
    else:
        proc.pulse_frequency.float_value = 42
        proc.pulse_duration.float_value = 12
        proc.pulsed_dim.float_value = 30

    tree = w.to_tree()

    if write_file:
        tree = {
            key: value
            for key, value in weldx.WeldxFile(tree=tree, mode="rw").items()
            if key not in ("asdf_library", "history")
        }

    w2 = WidgetGMAW()
    w2.from_tree(tree)

    assert w2.to_tree() == tree


def test_lang():
    """Test translation."""
    with voila_language(lang="de"):
        w = WidgetGMAW(process_type="spray")
    assert w.welding_wire.diameter.text == "Durchmesser"
