import ipywidgets as widgets
from ipywidgets import HBox, Label, Text

# TODO: factory pattern.
from widget_groove_sel import description_layout, textbox_layout


def hbox_float_text_creator(text, unit, value=7.5, min=0):
    hbox = HBox(
        [
            Label(text + " :", layout=description_layout),
            widgets.BoundedFloatText(value=value, min=min, layout=textbox_layout),
            Text(value=unit, placeholder="unit", layout=textbox_layout),
        ]
    )
    return hbox