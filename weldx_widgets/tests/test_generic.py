"""Tests for generic widgets."""

import pandas as pd

import weldx
from weldx_widgets import WidgetTimeSeries
from weldx_widgets.generic import is_safe_nd_array


def test_import_export():
    """Test import/export of WidgetTimeSeries."""
    data = [42, 23, 12]
    time = [0, 2, 4]
    ts = weldx.TimeSeries(weldx.Q_(data, "m"), time=pd.TimedeltaIndex(time, unit="s"))
    w = WidgetTimeSeries("m")
    w.from_tree(dict(timeseries=ts))
    assert w.base_unit.text_value == "m"
    assert w.base_data.text_value == str(data)
    assert w.time_data.text_value == str(time)

    ts2 = w.to_tree()
    assert ts2["timeseries"] == ts


def test_is_safe_nd_array():
    assert is_safe_nd_array("1, 2, 3")
    assert is_safe_nd_array("[1, 2, 3]")
    assert is_safe_nd_array("[[1, 2, 3], [4, 5, 6]]")
    assert is_safe_nd_array("[[1.2e3, -4.5E-2], [3.4]]")
    assert not is_safe_nd_array("[1, 2, 'evil']")
    assert not is_safe_nd_array("1, 2, (x) => x")
