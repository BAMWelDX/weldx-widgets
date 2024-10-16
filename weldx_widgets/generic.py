"""Generic widgets."""

import base64
import contextlib
import hashlib
from functools import partial
from typing import Callable, Optional

from ipyfilechooser import FileChooser
from IPython import get_ipython
from ipywidgets import HTML, Button, HBox, Label

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
    "download_button",
]


@contextlib.contextmanager
def show_only_exception_message():
    ip = get_ipython()
    if ip:
        old_state = ip.showtraceback
        f = ip.showtraceback
        tb = partial(f, exception_only=True)
        ip.showtraceback = tb

        yield

        ip.showtraceback = old_state
    else:
        yield


class WidgetSaveButton(WidgetMyHBox):
    """Widget to select an output file and save it."""

    def __init__(
        self,
        desc="Save to",
        filename="out.wx",
        path=".",
        filter_pattern=None,
        select_default=False,
    ):
        from weldx_widgets.widget_factory import button_layout

        self.file_chooser = FileChooser(
            path=path,
            filename=filename,
            filter_pattern=filter_pattern,
            select_default=select_default,
            select_desc="Select",
            change_desc="Change",
        )
        self.button = Button(description=desc, layout=button_layout)

        super().__init__(children=(self.file_chooser, self.button))

    def set_handler(self, handler: Callable):
        """Set action handler on save button click."""
        self.button.on_click(handler)

    @property
    def desc(self):
        """Save button description."""
        return self.button.desc

    @desc.setter
    def desc(self, value):
        self.button.desc = value

    @property
    # TODO: this should be named selected or better "value" to match ipywidgets style.
    def path(self):
        """Return selected file."""
        return self.file_chooser.selected


class WidgetTimeSeries(WidgetMyVBox, WeldxImportExport):
    """Preliminary time series editing widget."""

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
        super().__init__(children=children)

    def to_tree(self) -> dict:
        """Get mapping of input fields."""
        from weldx import Q_, TimeSeries

        # TODO: eval - the root of evil!
        base_data = self.convert_to_numpy_array(self.base_data.text_value)
        time_data = self.convert_to_numpy_array(self.time_data.text_value)
        ts = TimeSeries(
            data=Q_(base_data, units=self.base_unit.text_value),
            time=Q_(time_data, units=self.time_unit.text_value),
        )
        return {"timeseries": ts}

    @staticmethod
    def convert_to_numpy_array(input_str):
        import numpy as np
        try:
            # Step 1: Remove any unwanted characters and split by commas
            cleaned_input = input_str.strip().replace("\n", " ")

            # Step 2: Split the input string into individual elements
            input_list = [x.strip() for x in cleaned_input.split(",") if x]

            # Step 3: Convert each element to either int or float based on its format
            def convert_value(val):
                if '.' in val:  # If a decimal point is present, treat as float
                    return float(val)
                else:
                    return int(val)  # Otherwise, treat as int

            # Step 4: Apply the conversion and create a NumPy array with inferred types
            num_array = np.array([convert_value(x) for x in input_list], dtype=object)

            return num_array
        except ValueError:
            print("Error: Invalid input. Please ensure all values are numeric (int or float).")
            return None

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


def download_button(
    content: bytes,
    filename: str,
    button_description: str,
    html_instance: Optional[HTML] = None,
) -> HTML:
    """Load data from buffer into base64 payload embedded into an HTML button.

    Parameters
    ----------
    content :
        file contents as bytes.
    filename :
        The name when it is downloaded.
    button_description :
        The text that goes into the button.
    html_instance :
        update a passed instance or create a new one.
    """
    digest = hashlib.md5(content).hexdigest()  # bypass browser cache
    payload = base64.b64encode(content).decode()
    id_dl = f"dl_{digest}"
    html_button = f"""<html>
    <head>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    </head>
    <body>
    <a id={id_dl} download="{filename}" href="data:text/text;base64,{payload}" >
    <button class="p-Widget jupyter-widgets jupyter-button widget-button mod-success">
    {button_description}</button>
    </a>
    </body>
    </html>
    """
    if html_instance is None:
        html_instance = HTML()

    html_instance.value = html_button
    return html_instance
