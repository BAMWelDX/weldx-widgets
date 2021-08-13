import enum

from docutils.nodes import description

from weldx_widgets.widget_factory import FloatWithUnit, make_title, \
    WidgetLabeledTextInput

from ipywidgets import Checkbox, HBox, Dropdown, IntSlider, VBox, Layout, HTML, Button
from weldx.asdf.tags.weldx.aws import (
    GasComponent,
    ShieldingGasType,
    ShieldingGasForProcedure,
)
from weldx_widgets.widget_factory import description_layout

from weldx_widgets.widget_base import WidgetMyHBox, WidgetMyVBox, WeldxImportExport
from weldx import Q_

__all__ = [
    "WidgetSimpleGasSelection",
    "WidgetGasSelection",
]


class WidgetSimpleGasSelection(WidgetMyVBox):
    """Models a simple gas component.

    A gas component is a list of gases (element, percentage)
    """

    gas_list = ["Argon", "CO2", "Helium", "Hydrogen", "Oxygen"]
    _asdf_names = ['argon', 'carbon dioxide', 'helium', 'hydrogen', 'oxygen']
    _mapping = {gui_name:_asdf_name for gui_name, _asdf_name in zip(gas_list, _asdf_names)}

    def __init__(self, index=0):
        # create first gas dropdown, with buttons to delete and add gases.
        gas = self._create_gas_dropdown(index, percentage=100)
        self.components = {self.gas_list[index]: gas}

        super(WidgetSimpleGasSelection, self).__init__(
            children=[gas]
        )

    def _create_gas_dropdown(self, index=0, percentage=100):
        gas_dropdown = Dropdown(
            options=self.gas_list,
            value=self.gas_list[index],
            description="Gas",
            layout=description_layout,
            style={"description_width": "initial"},
        )

        percentage = IntSlider(start=0, end=100, value=percentage, desc="percentage")

        self.gas_selection = gas_dropdown

        button_add = Button(description="+")
        button_add.on_click(self._add_gas_comp)

        button_del = Button(description="-")
        box = HBox((gas_dropdown, percentage, button_add, button_del))

        # delete button
        from functools import partial
        handler = partial(self._del_gas_comp, box_to_delete=box)
        button_del.on_click(handler)

        return box

    def _del_gas_comp(self, button, box_to_delete):
        # TODO: do not delete the last one, or we are doomed :D
        new_children = [c for c in self.children if c is not box_to_delete]
        dropdown: Dropdown = box_to_delete.children[0]
        key = dropdown.value
        del self.components[key]
        self.children = new_children

    def _add_gas_comp(self, change):
        # find gas which not yet added
        # create gas dropdown
        not_chosen = list(set(self.gas_list) - set(self.components.keys()))
        if len(not_chosen) == 0:
            return
        gas_name = not_chosen[0]
        index_first_avail = self.gas_list.index(gas_name)
        box = self._create_gas_dropdown(index_first_avail)

        self.children += (box,)
        self.components[gas_name] = box

    def to_tree(self):
        gas_comp = [
            GasComponent(self._mapping[element], Q_(int(widget.children[1].value), "percent"))
            for element, widget in self.components.items()
        ]
        return dict(gas_component=gas_comp)


class WidgetShieldingGas(WidgetMyVBox):

    # TODO: this could in principle be used multiple times for all positions, torch, trailing, backing
    def __init__(self, position="torch"):
        self.flowrate = FloatWithUnit("Flow rate", "l/min", value=20)
        self.gas_components = WidgetSimpleGasSelection()

        children = [self.gas_components, self.flowrate]
        super(WidgetShieldingGas, self).__init__(children=children)

    def to_tree(self):
        gas_for_proc = ShieldingGasForProcedure(
            use_torch_shielding_gas=True,
            torch_shielding_gas=ShieldingGasType(
                **self.gas_components.to_tree(),
                common_name="SG"
            ),
            torch_shielding_gas_flowrate=self.flowrate.quantity)
        return dict(shielding_gas=gas_for_proc)


WidgetGasSelection = WidgetShieldingGas

if __name__ == "__main__":
    w = WidgetGasSelection()
    print(w.to_tree())
