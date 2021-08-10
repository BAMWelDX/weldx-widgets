import contextlib
from functools import partial

from IPython import get_ipython
from ipyfilechooser import FileChooser
from ipywidgets import HBox, Button

from weldx_widgets import WidgetLabeledTextInput
from weldx_widgets.widget_base import WidgetSimpleOutput, WidgetMyVBox
from weldx_widgets.widget_factory import textbox_layout, copy_layout

__all__ = ["WidgetSaveButton"]


@contextlib.contextmanager
def show_only_exception_message():
    ip = get_ipython()
    old_state = ip.showtraceback
    f = ip.showtraceback
    tb = partial(f, exception_only=True)
    ip.showtraceback = tb

    yield

    ip.showtraceback = old_state


# TODO: allow save and load with a switch!
class WidgetSaveButton(WidgetSimpleOutput):
    def __init__(self, desc="Save to", filename="out.txt", path=None):
        super(WidgetSaveButton, self).__init__()

        with self.out:
            self.file_chooser = FileChooser(path=path, filename=filename)
            self.button = w.Button(desc=desc)

        self.file_chooser.observe(self._chose_file, "selected_file")  # TODO: or value?

    def _chose_file(self):
        # TODO: pre-validate the path, e.g. writeable.
        pass

    @property
    def desc(self):
        return self.button.desc

    @desc.setter
    def desc(self, value):
        self.button.desc = value

    @property
    def path(self):
        return self.file_chooser.selected_path

    @path.setter
    def path(self, value):
        self.file_chooser.default_path = value


class WidgetTimeSeries(WidgetMyVBox):

    # TODO: handle math-expr
    def __init__(self, base_unit, time_unit="s", base_data="40, 20", time_data="0, 10"):
        layout_prefilled_text = copy_layout(textbox_layout)
        layout_prefilled_text.width = "300px"

        self.base_data = WidgetLabeledTextInput(
            label_text="Base data expr", prefilled_text=base_data
        )
        self.time_data = WidgetLabeledTextInput(
            label_text="Time data expr", prefilled_text=time_data
        )
        self.base_data.text.layout = layout_prefilled_text
        self.time_data.text.layout = layout_prefilled_text

        self.time_unit = WidgetLabeledTextInput(
            label_text="Time unit", prefilled_text=time_unit
        )
        self.base_unit = WidgetLabeledTextInput(
            label_text="Base unit", prefilled_text=base_unit
        )

        self.button = Button(description="eval")
        self.button.on_click(self.to_tree)
        self.out = WidgetSimpleOutput()
        children = [
            HBox([self.base_data, self.base_unit]),
            HBox([self.time_data, self.time_unit]),
            self.button,
            self.out,
        ]
        super(WidgetTimeSeries, self).__init__(children=children)

    def to_tree(self, *args, **kwargs):
        from weldx import TimeSeries, Q_

        with self.out:
            # TODO: eval - the root of evil!
            ts = TimeSeries(
                data=Q_(
                    eval(self.base_data.text_value), units=self.base_unit.text_value
                ),
                time=Q_(
                    eval(self.time_data.text_value), units=self.time_unit.text_value
                ),
            )
        return {"timeseries": ts}


if __name__ == "__main__":
    w = WidgetTimeSeries("V", "s")
    print(w.to_tree())
