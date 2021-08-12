import ipywidgets as widgets
from ipywidgets import HBox, Label, Text, Layout, HTML

from weldx import Q_

from weldx_widgets.widget_base import WidgetMyHBox

plot_layout = Layout(width="60%", height="550px")
button_layout = Layout(width="200px", height="50px")
textbox_layout = Layout(width="50px", height="30px")  # used for units
description_layout = Layout(width="30%", height="30px")

layout_generic_output = Layout(width="50%", height="300px")


def copy_layout(layout):
    # TODO: this is very primitive!
    return Layout(height=layout.height, width=layout.width)


def hbox_float_text_creator(text, unit, value=7.5, min=0, make_box=True):
    children = [
        Label(text, layout=description_layout),
        widgets.BoundedFloatText(value=value, min=min, layout=textbox_layout),
        Text(value=unit, placeholder="unit", layout=textbox_layout),
    ]
    if make_box:
        return HBox(children=children)

    return children


class WidgetLabeledTextInput(WidgetMyHBox):
    def __init__(self, label_text, prefilled_text=None):
        self.label = Label(label_text, layout=description_layout)
        self.text = Text(value=prefilled_text, layout=textbox_layout)
        children = [self.label, self.text]
        super(WidgetLabeledTextInput, self).__init__(children=children)

    @property
    def text_value(self):
        return self.text.value

    @text_value.setter
    def text_value(self, value):
        self.text.value = value


class FloatWithUnit(WidgetMyHBox):
    def __init__(self, text, unit, value=0, min=0):
        self._label, self._float, self._unit = hbox_float_text_creator(
            text, unit, value, min, make_box=False
        )
        super(FloatWithUnit, self).__init__(
            children=[self._label, self._float, self._unit]
        )

    @property
    def text(self):
        return self._label.value

    @text.setter
    def text(self, value):
        self._label.value = value

    @property
    def unit(self) -> Q_:
        return Q_(self._unit.value)

    @unit.setter
    def unit(self, value):
        self._unit.value = str(Q_(value))

    @property
    def float_value(self) -> float:
        return float(self._float.value)

    @float_value.setter
    def float_value(self, value):
        self._float.value = value

    @property
    def quantity(self) -> Q_:
        return Q_(self.float_value, self.unit)


def make_title(text, heading_level=3):
    return HTML(f"<h{heading_level}>{text}</h{heading_level}>")
