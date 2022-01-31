"""Factory for commonly used widget elements."""
import contextlib

import ipywidgets as widgets
from ipywidgets import HTML, Label, Layout, Text
from traitlets import All, HasTraits

from weldx import Q_, TimeSeries
from weldx_widgets.widget_base import WidgetMyHBox

plot_layout = Layout(width="60%", height="550px")
button_layout = Layout(
    # width="200px",
    width="auto",
    # height="50px",
)
textbox_layout = Layout(width="65px", height="30px")  # used for units
description_layout = Layout(width="35%", height="30px")

layout_generic_output = Layout(width="50%", height="300px")


def copy_layout(layout):
    """Copy given layout."""
    # TODO: this is very primitive!
    return Layout(height=layout.height, width=layout.width)


@contextlib.contextmanager
def temporarily_unobserve_all(widget):
    """Block all events within the context."""
    from traitlets import HasTraits

    if not isinstance(widget, HasTraits):
        raise ValueError(f"unsupported type {type(widget)}")
    if not widget._trait_notifiers:
        yield
    else:
        old = widget._trait_notifiers
        widget._trait_notifiers = {}
        yield
        widget._trait_notifiers = old


class WidgetLabeledTextInput(WidgetMyHBox):
    """Widget for labeled Text."""

    def __init__(self, label_text, prefilled_text=None):
        self.label = Label(label_text, layout=description_layout)
        self.text = Text(value=prefilled_text, layout=textbox_layout)
        children = [self.label, self.text]
        super(WidgetLabeledTextInput, self).__init__(children=children)

    @property
    def text_value(self) -> str:
        """Return text value of input field."""
        return self.text.value

    @text_value.setter
    def text_value(self, value):
        self.text.value = value


class FloatWithUnit(WidgetMyHBox):
    """Widget grouping a float with unit."""

    def __init__(self, text, unit, value: float = 0.0, min=0):
        self._label = Label(text, layout=description_layout)
        self._float = widgets.BoundedFloatText(
            value=value, min=min, max=2**32, layout=textbox_layout
        )
        self._unit = Text(value=unit, placeholder="unit", layout=textbox_layout)

        super(FloatWithUnit, self).__init__(
            children=[self._label, self._float, self._unit],
        )

    def observe_float_value(self, handler, names=All, type="change"):  # noqa
        self._float.observe(handler, names, type)

    observe_float_value.__doc__ = HasTraits.observe.__doc__

    def observe_unit(self, handler, names=All, type="change"):  # noqa
        self._unit.observe(handler, names, type)

    observe_unit.__doc__ = HasTraits.observe.__doc__

    @contextlib.contextmanager
    def silence_events(self):
        """Do not listen to events within this context."""
        with contextlib.ExitStack() as stack:
            stack.enter_context(temporarily_unobserve_all(self._unit))
            stack.enter_context(temporarily_unobserve_all(self._float))
            yield

    @property
    def text(self):
        """Return description/label value."""
        return self._label.value

    @text.setter
    def text(self, value):
        self._label.value = value

    @property
    def unit(self) -> Q_:
        """Return unit of this float."""
        return Q_(self._unit.value)

    @unit.setter
    def unit(self, value):
        self._unit.value = str(Q_(value))

    @property
    def float_value(self) -> float:
        """Return float value."""
        return float(self._float.value)

    @float_value.setter
    def float_value(self, value):
        self._float.value = value

    @property
    def quantity(self) -> Q_:
        """Return wrapped quantity of this float."""
        return Q_(self.float_value, self.unit)

    @quantity.setter
    def quantity(self, value):
        self.float_value = value.magnitude
        self.unit = value.units

    def as_time_series(self) -> TimeSeries:
        """Wrap the quantity as weldx.TimeSeries."""
        return TimeSeries(self.quantity)


def make_title(text, heading_level=3):
    """Return an HTML formatted heading."""
    from weldx_widgets.translation_utils import _i18n as _

    return HTML(f"<h{heading_level}>{_(text)}</h{heading_level}>")
