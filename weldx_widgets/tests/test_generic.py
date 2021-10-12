"""Tests for generic widgets."""
import pandas as pd

import weldx
from weldx_widgets import WidgetTimeSeries


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
