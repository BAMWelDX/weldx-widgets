"""Widgets to handle shielding gas selection."""
from ipywidgets import Button, Dropdown, HBox, IntSlider, Layout, Output

from weldx import Q_
from weldx.tags.aws import GasComponent, ShieldingGasForProcedure, ShieldingGasType
from weldx_widgets.widget_base import WidgetMyVBox
from weldx_widgets.widget_factory import (
    FloatWithUnit,
    button_layout,
    description_layout,
)

__all__ = ["WidgetShieldingGas"]


class WidgetSimpleGasSelection(WidgetMyVBox):
    """Models a simple gas component.

    A gas component is a list of gases (element, percentage)
    """

    gas_list = ["Argon", "CO2", "Helium", "Hydrogen", "Oxygen"]
    _asdf_names = ["argon", "carbon dioxide", "helium", "hydrogen", "oxygen"]
    _mapping = {
        gui_name: _asdf_name for gui_name, _asdf_name in zip(gas_list, _asdf_names)
    }

    def __init__(self, index=0, percentage=100):
        # create first gas dropdown, with buttons to delete and add gases.
        gas = self._create_gas_dropdown(index, percentage=percentage)
        self.initial_percentage = percentage
        self.components = {self.gas_list[index]: gas}

        self.out = Output(
            layout=Layout(
                width="auto", height="80px", display="none", border="2px solid"
            )
        )

        button_add = Button(description="Add gas component")
        button_add.on_click(self._add_gas_comp)

        super(WidgetSimpleGasSelection, self).__init__(children=[button_add, gas])

    def _create_gas_dropdown(self, index=0, percentage=100):
        gas_dropdown = Dropdown(
            options=self.gas_list,
            value=self.gas_list[index],
            description="Gas",
            layout=description_layout,
            style={"description_width": "initial"},
        )

        percentage = IntSlider(
            start=0, end=100, value=percentage, description="percentage"
        )
        percentage.observe(self._check, type="change")

        self.gas_selection = gas_dropdown

        button_del = Button(description="delete", layout=button_layout)

        box = HBox((gas_dropdown, percentage, button_del))

        # delete button
        from functools import partial

        handler = partial(self._del_gas_comp, box_to_delete=box)
        button_del.on_click(handler)

        return box

    def _del_gas_comp(self, button, box_to_delete):
        new_children = [c for c in self.children if c is not box_to_delete]
        dropdown: Dropdown = box_to_delete.children[0]
        key = dropdown.value
        del self.components[key]
        self.children = new_children

    def _add_gas_comp(self, change):
        # find gas which was not yet added
        not_chosen = list(set(self.gas_list) - set(self.components.keys()))
        if len(not_chosen) == 0:
            return
        gas_name = not_chosen[0]
        index_first_avail = self.gas_list.index(gas_name)
        box = self._create_gas_dropdown(index_first_avail, percentage=0)

        self.children += (box,)
        self.components[gas_name] = box

    def _check(self, value):
        gas_components = self.to_tree()["gas_component"]
        if not sum(g.gas_percentage for g in gas_components) == 100:
            with self.out:
                print(
                    "Check percentages, all components should sum up to 100!"
                )  # , file=sys.stderr)
        else:
            # remove output, if everything is alright.
            self.out.clear_output()
            self.out.layout.display = "none"

    def to_tree(self) -> dict:
        gas_components = [
            GasComponent(
                self._mapping[element], Q_(int(widget.children[1].value), "percent")
            )
            for element, widget in self.components.items()
        ]
        return dict(gas_component=gas_components)


class WidgetShieldingGas(WidgetMyVBox):
    """Widget to combine flow rate with a gas selection."""

    # TODO: this could in principle be used multiple times for all positions
    #  e.g. torch, trailing, backing
    def __init__(self, position="torch"):
        self.flowrate = FloatWithUnit("Flow rate", "l/min", value=20)
        self.gas_components = WidgetSimpleGasSelection()

        children = [self.gas_components, self.flowrate]
        super(WidgetShieldingGas, self).__init__(children=children)

    def to_tree(self) -> dict:
        """Return weldx objects describing the shielding gas."""
        gas_for_proc = ShieldingGasForProcedure(
            use_torch_shielding_gas=True,
            torch_shielding_gas=ShieldingGasType(
                **self.gas_components.to_tree(), common_name="SG"
            ),
            torch_shielding_gas_flowrate=self.flowrate.quantity,
        )
        return dict(shielding_gas=gas_for_proc)


def test():
    w = WidgetShieldingGas()
    w.to_tree()
