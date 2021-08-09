from ipywidgets import Checkbox, HBox, Dropdown, IntSlider, VBox
from weldx.asdf.tags.weldx.aws import (
    GasComponent,
    ShieldingGasType,
    ShieldingGasForProcedure,
)
from weldx_widgets.widget_factory import description_layout

from weldx_widgets.widget_base import WidgetSimpleOutput
from weldx import Q_

# TODO: even simpler just one chooser?! then combine?!?

"""
class ShieldingGasForProcedure:

    use_torch_shielding_gas: bool
    torch_shielding_gas: ShieldingGasType
    torch_shielding_gas_flowrate: pint.Quantity
    
    [[use_backing_gas: bool = None
    backing_gas: ShieldingGasType = None
    backing_gas_flowrate: pint.Quantity = None]]
    
    use_trailing_gas: bool = None
    trailing_shielding_gas: ShieldingGasType = None
    trailing_shielding_gas_flowrate: pint.Quantity = None
    
3. gase, toggle
"""

# TODO: simple: one gas + flow rate!
class WidgetGasSelection(WidgetSimpleOutput):
    gas_list = ["Argon", "CO2", "Helium", "Hydrogen", "Oxygen", None]

    def __init__(self, gas_name, enabled=True):
        super(WidgetGasSelection, self).__init__()
        self.use_gas = Checkbox(
            value=enabled, description=f"Use {gas_name} gas"
        )

        self.gas_box = self._create_gas_dropdown(0, 80)
        self.box = HBox([self.use_gas, self.gas_box])

        def toggle_use_gas(change):
            value = change["new"]
            self.gas_box.layout.visible = value

        self.use_gas.observe(toggle_use_gas, "value")

    @property
    def use_torch_shielding_gas(self):
        return self.use_torch_shielding_gas.value

    def _create_gas_dropdown(self, index=0, percentage=80):
        gas_list = WidgetGasSelection.gas_list

        gas_dropdown1 = Dropdown(
            options=gas_list,
            value=gas_list[index],
            description="1. Shielding gas:",
            layout=description_layout,
            style={"description_width": "initial"},
        )

        gas_dropdown2 = Dropdown(
            options=gas_list,
            value=gas_list[index + 1],
            description="2. Shielding gas:",
            layout=description_layout,
            style={"description_width": "initial"},
        )

        slider1 = IntSlider(start=0, end=100, value=percentage)
        slider2 = IntSlider(start=0, end=100, value=100 - percentage)
        container1 = HBox((gas_dropdown1, slider1))
        container2 = HBox((gas_dropdown2, slider2))

        def update(change):
            owner = change["owner"]
            to_change = slider1 if owner is slider2 else slider2
            to_change.value = 100 - change["new"]
            assert slider1 + slider2 == 100

        slider1.observe(update, "value")
        slider2.observe(update, "value")

        self._gas1 = gas_dropdown1
        self._gas2 = gas_dropdown2
        self._gas1_percentage = slider1
        self._gas2_percentage = slider2

        box = VBox([container1, container2])
        return box

    @property
    def gas_1(self):
        return self._gas1.value

    @property
    def gas_2(self):
        return self._gas2.value

    @property
    def gas_1_percentage(self):
        return self._gas1_percentage.value

    @property
    def gas_2_percentage(self):
        return self._gas2_percentage.value


    # TODO: flow rate should be obtain from a widget!
    def to_tree(
        self, flow_rate: Q_ = Q_(20, "l / min"), use_torch_shielding_gas: bool = True
    ):

        gas_comp = [
            GasComponent(self.gas_1, Q_(self.gas_1_percentage, "percent")),
            GasComponent(self.gas_2, Q_(self.gas_2_percentage, "percent")),
        ]
        gas_type = ShieldingGasType(gas_component=gas_comp, common_name="SG")

        gas_for_procedure = ShieldingGasForProcedure(
            use_torch_shielding_gas=use_torch_shielding_gas,
            torch_shielding_gas=gas_type,
            torch_shielding_gas_flowrate=flow_rate,
        )
        # TODO: wrap inside a dict according to schema!
        return gas_for_procedure

    def display(self):
        from IPython.core.display import display

        display(self.box)
