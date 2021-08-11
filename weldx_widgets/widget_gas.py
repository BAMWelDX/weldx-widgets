from weldx_widgets.widget_factory import FloatWithUnit, make_title

from ipywidgets import Checkbox, HBox, Dropdown, IntSlider, VBox, Layout, HTML
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


class WidgetSimpleGasSelection(WidgetMyHBox):
    """Models a simple gas component.

    A gas component is a list of gases (element, percentage)
    TODO: this is currently wrongly implemented...
    """

    gas_list = ["Argon", "CO2", "Helium", "Hydrogen", "Oxygen", None]

    def __init__(self, index=0, percentage=80):
        self.gas_box = self._create_gas_dropdown(index, percentage)
        self._flow_rate = FloatWithUnit(text="flow rate", value=20, min=0, unit="l/min")

        super(WidgetSimpleGasSelection, self).__init__(
            children=(self.gas_box, self._flow_rate)
        )

    def _create_gas_dropdown(self, index=0, percentage=100):
        gas_list = WidgetSimpleGasSelection.gas_list

        gas_dropdown = Dropdown(
            options=gas_list,
            value=gas_list[index],
            description="Gas:",
            layout=description_layout,
            style={"description_width": "initial"},
        )

        percentage = IntSlider(start=0, end=100, value=percentage, desc="percentage")
        box = HBox((gas_dropdown, percentage))

        self.gas_selection = gas_dropdown
        self._percentage = percentage

        return box

    @property
    def selected_gas(self):
        return self.gas_selection.value

    @property
    def percentage(self) -> Q_:
        return Q_(self._percentage.value, "%")

    @property
    def flow_rate(self):
        return Q_(self._flow_rate.float_value, self._flow_rate.unit)

    def to_tree(self):
        gas_comp = [
            GasComponent(self.selected_gas, Q_(self.percentage, "percent")),
        ]
        gas_type = ShieldingGasType(gas_component=gas_comp, common_name="SG")

        return dict(gas_component=gas_type)


class WidgetGasSelection(WidgetMyVBox, WeldxImportExport):

    gas_usages = ("Torch shielding gas", "Backing gas", "Trailing shielding gas")
    schema_names = ("use_torch_shielding_gas", "use_backing_gas", "use_trailing_gas")

    def __init__(self):
        gas_boxes = []
        for i, (g, s) in enumerate(
            zip(
                WidgetGasSelection.gas_usages,
                WidgetGasSelection.schema_names,
            )
        ):
            use_gas = Checkbox(value=i == 0, description=f"Use {g}?")
            gas_sel = WidgetSimpleGasSelection(index=i)
            setattr(self, f"_{s[4:]}", gas_sel)
            setattr(self, f"_{s}", use_gas)

            def toggle_use_gas(change):
                value = change["new"]
                gas_sel.layout.visible = value

            use_gas.observe(toggle_use_gas, "value")
            box = HBox([use_gas, gas_sel])
            gas_boxes.append(box)
        super(WidgetGasSelection, self).__init__(
            children=[
                make_title("Welding gases"),
                *gas_boxes,
            ]
        )

    @property
    def use_torch_shielding_gas(self):
        return self._use_torch_shielding_gas

    @property
    def use_backing_gas(self):
        return self._use_backing_gas

    @property
    def use_trailing_gas(self):
        return self._use_trailing_gas

    @property
    def torch_shielding_gas(self):
        return self._torch_shielding_gas

    @property
    def backing_gas(self):
        return self._backing_gas

    @property
    def trailing_gas(self):
        return self._trailing_gas

    def to_tree(self) -> dict:
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
        """
        gas_for_procedure = ShieldingGasForProcedure(
            use_torch_shielding_gas=self.use_torch_shielding_gas,
            torch_shielding_gas=ShieldingGasType(
                **self.torch_shielding_gas.to_tree(), common_name="SG"
            ),
            torch_shielding_gas_flowrate=self.torch_shielding_gas,
        )

        if self.use_backing_gas:
            gas_for_procedure.use_backing_gas = True
            gas_for_procedure.backing_gas = ShieldingGasType(
                **self.backing_gas.to_tree(),
                common_name="BG",
            )
        if self.use_trailing_gas:
            gas_for_procedure.use_trailing_gas = True
            gas_for_procedure.backing_gas = ShieldingGasType(
                **self.trailing_gas.to_tree(),
                common_name="TG",
            )
        return {"shielding_gas": gas_for_procedure}

    def from_tree(self, tree: dict):
        sg = tree["shielding_gas"]
        # self._use_torch_shielding_gas = sg["use_torch_shielding_gas"]

    @property
    def schema(self) -> str:
        pass


if __name__ == "__main__":
    w = WidgetGasSelection()
    print(w.to_tree())
