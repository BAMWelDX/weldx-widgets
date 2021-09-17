"""Generic widgets."""
import contextlib
from functools import partial

from ipyfilechooser import FileChooser
from IPython import get_ipython
from ipywidgets import Button, HBox, Label

import weldx
from weldx_widgets.widget_base import WeldxImportExport, WidgetMyHBox, WidgetMyVBox
from weldx_widgets.widget_factory import (
    WidgetLabeledTextInput,
    copy_layout,
    textbox_layout,
)

__all__ = [
    "WidgetSaveButton",
    "WidgetTimeSeries",
]


@contextlib.contextmanager
def show_only_exception_message():
    ip = get_ipython()
    old_state = ip.showtraceback
    f = ip.showtraceback
    tb = partial(f, exception_only=True)
    ip.showtraceback = tb

    yield

    ip.showtraceback = old_state


class WidgetSaveButton(WidgetMyHBox):
    """Widget to select an output file and save it."""

    def __init__(self, desc="Save to", filename="out.wx", path=".", file_pattern=None):
        from weldx_widgets.widget_factory import button_layout

        self.file_chooser = FileChooser(
            path=path, filename=filename, file_pattern=file_pattern
        )
        self.button = Button(description=desc, layout=button_layout)

        super(WidgetSaveButton, self).__init__(
            children=(self.file_chooser, self.button)
        )

    @property
    def desc(self):
        """Save button description."""
        return self.button.desc

    @desc.setter
    def desc(self, value):
        self.button.desc = value

    @property
    def path(self):
        """Return selected file."""
        return self.file_chooser.selected


class WidgetTimeSeries(WidgetMyVBox, WeldxImportExport):
    """Preliminary time series editing widget."""

    @property
    def schema(self) -> str:
        """Return schema to validate data against."""
        return "time_series-1.0.0"

    # TODO: handle math-expr
    def __init__(
        self, base_unit, time_unit="s", base_data="0", time_data="0", title=""
    ):
        layout_prefilled_text = copy_layout(textbox_layout)
        layout_prefilled_text.width = "300px"

        self.base_data = WidgetLabeledTextInput(
            label_text="Input dimension", prefilled_text=base_data
        )
        self.time_data = WidgetLabeledTextInput(
            label_text="Time steps", prefilled_text=time_data
        )
        self.base_data.text.layout = layout_prefilled_text
        self.time_data.text.layout = layout_prefilled_text

        self.time_unit = WidgetLabeledTextInput(label_text="", prefilled_text=time_unit)
        self.base_unit = WidgetLabeledTextInput(label_text="", prefilled_text=base_unit)

        children = [
            HBox([self.base_data, self.base_unit]),
            HBox([self.time_data, self.time_unit]),
        ]
        if title:
            children.insert(0, Label(title))
        super(WidgetTimeSeries, self).__init__(children=children)

    def to_tree(self) -> dict:
        """Get mapping of input fields."""
        from weldx import Q_, TimeSeries

        # TODO: eval - the root of evil!
        ts = TimeSeries(
            data=Q_(eval(self.base_data.text_value), units=self.base_unit.text_value),
            time=Q_(eval(self.time_data.text_value), units=self.time_unit.text_value),
        )
        return {"timeseries": ts}

    def from_tree(self, tree: dict):
        """Read in data from given dict."""
        ts: weldx.TimeSeries = tree["timeseries"]
        if ts.time is not None:
            foo = ", ".join(str(x) for x in ts.time.as_timedelta().seconds)
            self.time_data.text_value = f"[{foo}]"
        else:
            self.time_data.text_value = ""

        self.base_data.text_value = repr(list(ts.data.magnitude))
        self.base_unit.text_value = format(ts.data.units, "~")


def test_import_export():
    import pandas as pd

    import weldx

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
