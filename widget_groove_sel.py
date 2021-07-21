from __future__ import annotations

import ipywidgets as widgets
import matplotlib.pyplot as plt
import weldx
from IPython.display import clear_output, display
from ipywidgets import Button, HBox, Label, Layout, VBox
from weldx.constants import WELDX_QUANTITY as Q_
from weldx.welding.groove.iso_9692_1 import _groove_name_to_type, get_groove

from widget_factory import hbox_float_text_creator
from widget_base import WidgetSimpleOutput

# Layouts
# TODO: not global? can cause ugly side effects, better use a factory.
plot_layout = Layout(width="60%", height="550px")
button_layout = Layout(width="200px", height="50px")
textbox_layout = Layout(width="15%", height="30px")
description_layout = Layout(width="30%", height="30px")


def get_code_numbers():
    """The FFGroove type defines multiple code numbers"""
    from weldx.welding.groove.iso_9692_1 import FFGroove

    try:
        a = FFGroove.__annotations__
        return a["code_number"].__args__
    except:
        return [
            "1.12", "1.13", "2.12", "3.1.1", "3.1.2", "3.1.3", "4.1.1", "4.1.2", "4.1.3"
        ]


# TODO: nice group layout for all widgets
# TODO: reset button parameters (defaults).
class GrooveSelectionWidget(WidgetSimpleOutput):
    # TODO: filename/WeldxFile as input arg?
    def __init__(self):
        super(GrooveSelectionWidget, self).__init__()

        self.out.layout = plot_layout
        self.groove_obj = None  # current groove object
        self.hbox_dict = None  # TODO: better name

        # create figure for groove visualization
        self._create_plot()

        self.selected_values_vbox = VBox([])
        self.groove_type_dropdown = self._create_groove_dropdown()
        self.save_button = self._create_save_button()
        # create rest
        groove_selection = VBox([self.groove_type_dropdown, self.selected_values_vbox])
        self.boxed_widgets = VBox(
            [HBox([groove_selection, self.out]), self.save_button, self.button_o]
        )

        # set initial state
        self._update_params_to_selection(dict(new=self.groove_type_dropdown.value))
        self._update_plot(None)

    def _create_save_button(self):
        self.button_o = widgets.Output()
        self.filename = widgets.Text("groove.weldx", layout=description_layout)

        def on_button_clicked(_):
            # TODO: set output filename and save it!
            with self.button_o:
                clear_output()
                tree = {"groove": self.groove_obj}
                print("vis tree....")
                with weldx.WeldxFile(
                    tree=tree, mode="rw"
                ) as fh:
                    fh.show_asdf_header(True, True)

        # button
        b = Button(description="Show as .yml File", layout=button_layout)
        b.on_click(on_button_clicked)

        box = VBox([self.filename, b, self.button_o])
        return box

    def _create_plot(self):
        with self.out:
            self.fig, self.ax = plt.subplots(1, 1, figsize=(5, 4), dpi=100)
            canvas = self.fig.canvas
            canvas.toolbar_visible = False
            canvas.header_visible = False
            canvas.footer_visible = False
            canvas.resizable = False
            #plt.show(self.fig)

    def _create_groove_dropdown(self):
        # get all attribute mappings (human-readable names)
        attrs = {
            attr
            for groove in _groove_name_to_type
            for attr in _groove_name_to_type[groove]._mapping.values()
        }

        # create dict with hboxes of all attributes
        self.hbox_dict = dict()
        hbox_dict = self.hbox_dict
        with self.out:
            for item in attrs:
                if item == "code_number":
                    dropdown = widgets.Dropdown(
                        # import those somewhere?
                        options=get_code_numbers(),
                        layout=description_layout,
                    )
                    hbox_dict[item] = HBox(
                        [Label("code_number :", layout=description_layout), dropdown]
                    )
                elif "angle" in item:
                    hbox_dict[item] = hbox_float_text_creator(item, "deg", 45)
                elif "workpiece_thickness" in item:
                    hbox_dict[item] = hbox_float_text_creator(item, "mm", 15)
                else:
                    hbox_dict[item] = hbox_float_text_creator(item, "mm", 5)

        groove_list = list(_groove_name_to_type.keys())
        # TODO: layout
        groove_type_dropdown = widgets.Dropdown(
            options=groove_list,
            value=groove_list[1],
            description="Groove type :",
        )

        # connect value observers
        groove_type_dropdown.observe(self._update_params_to_selection, names="value")

        update_plot = self._update_plot
        groove_type_dropdown.observe(update_plot, "value")
        for key, box in hbox_dict.items():
            box.children[1].observe(update_plot, "value")
            if key != "code_number":
                box.children[2].observe(update_plot, "value")

        return groove_type_dropdown

    def _update_plot(
        self,
        _
    ):
        selection = self.groove_type_dropdown.value
        with self.out:
            get_groove_dict = dict()
            get_groove_dict["groove_type"] = selection
            for child in self.selected_values_vbox.children:
                child_0 = child.children[0]
                if child_0.value[:-2] == "code_number":
                    get_groove_dict[child_0.value[:-2]] = child.children[1].value
                else:
                    magnitude = child.children[1].value
                    unit = child.children[2].value
                    get_groove_dict[child_0.value[:-2]] = Q_(magnitude, unit)

            self.groove_obj = get_groove(**get_groove_dict)
            # TODO: replot can be avoided (e.g. set_xydata?)
            self.ax.lines = []
            #self.ax.texts = []
            from generic import show_only_exception_message
            with show_only_exception_message():
                self.groove_obj.plot(line_style="-", ax=self.ax)

    def _update_params_to_selection(self, change):
        selection = change["new"]
        self.selected_values_vbox.children = [
            slider
            for key, slider in self.hbox_dict.items()
            if key
            in (
                _groove_name_to_type[selection]._mapping[x]
                for x in _groove_name_to_type[selection]._mapping
               )
        ]

    def display(self):
        display(self.boxed_widgets)


class WidgetGrooveSelectionTCPMovement:
    def __init__(self):
        self.groove_sel = GrooveSelectionWidget()

        # TODO: add input fields for weld speed, seam length, tcp offsets (x, y, z). At libo lab we only use (y,z)
        epsilon = 1
        with self.groove_sel.out:
            self.weld_speed = hbox_float_text_creator("Weld speed", value=20, min=epsilon, unit="mm/s")
            self.seam_length = hbox_float_text_creator("Seam length", value=300, min=epsilon, unit="mm")

    def display(self):
        self.groove_sel.display()
        #display( *(self.weld_speed, self.seam_length))