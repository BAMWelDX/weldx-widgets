import ipywidgets as widgets
from ipywidgets import HBox, Label, Text, Layout


# TODO: factory pattern.
plot_layout = Layout(width="60%", height="550px")
button_layout = Layout(width="200px", height="50px")
textbox_layout = Layout(width="15%", height="30px")
description_layout = Layout(width="30%", height="30px")


def hbox_float_text_creator(text, unit, value=7.5, min=0):
    hbox = HBox(
        [
            Label(text + " :", layout=description_layout),
            widgets.BoundedFloatText(value=value, min=min, layout=textbox_layout),
            Text(value=unit, placeholder="unit", layout=textbox_layout),
        ]
    )
    return hbox
