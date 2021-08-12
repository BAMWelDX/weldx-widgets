from functools import lru_cache

import pytest
from ipywidgets import Dropdown
from matplotlib import pylab as plt

import weldx
from weldx import GmawProcess, Q_, TimeSeries
from weldx_widgets import WidgetGasSelection
from weldx_widgets.generic import WidgetTimeSeries
from weldx_widgets.widget_base import WidgetMyVBox, WeldxImportExport
from weldx_widgets.widget_factory import (
    FloatWithUnit,
    make_title,
    WidgetLabeledTextInput,
)


def parplot(par, t, name, ax):
    """plot a single parameter into an axis"""
    ts = par.interp_time(t)
    x = weldx.util.pandas_time_delta_to_quantity(t)
    ax.plot(x.m, ts.data.m)
    ax.set_ylabel(f"{name} / {ts.data.u:~}")
    ax.grid()


def plot_gmaw(gmaw, t):
    """Plot a dictionary of parameters"""

    title = "\n".join([gmaw.manufacturer, gmaw.power_source, gmaw.base_process])

    pars = gmaw.parameters
    n = len(pars)

    fig, ax = plt.subplots(nrows=n, sharex="all", figsize=(_DEFAULT_FIGWIDTH, 2 * n))
    for i, k in enumerate(pars):
        parplot(pars[k], t, k, ax[i])
    ax[-1].set_xlabel(f"time / s")
    ax[0].set_title(title, loc="left")

    # ipympl_style(fig)

    return fig, ax


class BaseProcess(WidgetMyVBox):
    def __init__(self):
        self.manufacturer = WidgetLabeledTextInput("Manufacturer", "Fronius")
        self.power_source = WidgetLabeledTextInput("Power source", "TPS 500i")
        self.wire_feedrate = FloatWithUnit(
            text="Wire feed rate", value=10, min=0, unit="m/min"
        )
        children = [
            self.manufacturer,
            self.power_source,
            self.wire_feedrate,
        ]
        super(BaseProcess, self).__init__(children=children)

    def to_tree(self):
        return dict(manufacturer=self.manufacturer.text_value,
                    powersource=self.power_source.text_value,
                    wire_feedrate=self.wire_feedrate.quantity,
                    )

    def from_tree(self, tree):
        raise NotImplementedError


class PulsedProcess(WidgetMyVBox):
    def __init__(self, kind="UI"):
        self.base_process = BaseProcess()
        self.pulse_duration = FloatWithUnit("Pulse duration", value=5.0, unit="ms")
        self.pulse_frequency = FloatWithUnit("Pulse frequency", value=100.0, unit="Hz")
        self.base_current = FloatWithUnit("Base current", value=60.0, unit="A")

        if kind == "UI":
            self.pulsed_dim = FloatWithUnit("Pulse voltage", "V", 40)
        elif kind == "II":
            self.pulsed_dim = FloatWithUnit("Pulse current", "A", 300)
        else:
            raise ValueError(f"unknown kind: {kind}")
        self.kind = kind
        self.tag = "CLOOS/pulse"
        self.meta = {"modulation": self.kind}

        children = [
            make_title(f"Pulsed ({self.kind}) process parameters"),
            self.base_process,
            self.pulse_duration,
            self.pulse_frequency,
            self.base_current,
            self.pulsed_dim
        ]
        super(PulsedProcess, self).__init__(children=children)

    def to_tree(self):
        base_params = self.base_process.to_tree()
        manufacturer = base_params.pop("manufacturer")
        power_source = base_params.pop("powersource")
        # these params have to be quantities
        params = dict(**base_params,
                      pulse_duration=self.pulse_duration.quantity,
                      pulse_frequency=self.pulse_frequency.quantity,
                      base_current=self.base_current.quantity,
                      )
        if self.kind == "UI":
            params["pulse_voltage"] = self.pulsed_dim.quantity
        else:
            params["pulse_current"] = self.pulsed_dim.quantity

        process = GmawProcess(
            base_process="pulse",
            manufacturer=manufacturer,
            power_source=power_source,
            parameters=params,
            tag="CLOOS/pulse",  # TODO: tag should match manufacturer
            meta={"modulation": self.kind},
        )
        return dict(process=process)


class ProcessSpray(WidgetMyVBox):
    def __init__(self):
        self.base_process = BaseProcess()
        self.voltage = WidgetTimeSeries(
            base_data="40.0, 20.0", base_unit="V", time_data="0.0, 10.0", time_unit="s"
        )
        self.impedance = FloatWithUnit(text="Impendance", value=10, unit="percent")
        self.characteristic = FloatWithUnit("Characteristic", value=5, unit="V/A")
        self.tag = "CLOOS/spray_arc"

        super(ProcessSpray, self).__init__(
            children=[
                make_title("Spray process parameters"),
                self.base_process,
                self.voltage,
                self.impedance,
                self.characteristic,
            ]
        )

    def to_tree(self):
        base_params = self.base_process.to_tree()
        manufacturer = base_params.pop("manufacturer")
        power_source = base_params.pop("powersource")
        # these params have to be quantities
        params = dict(**base_params,
                      voltage=self.voltage.to_tree()["timeseries"],
                      impedance=self.impedance.quantity,
                      characteristic=self.characteristic.quantity,
                      )
        tag = "CLOOS/spray"
        process = GmawProcess(manufacturer=manufacturer, power_source=power_source,
                              parameters=params, tag=tag)
        return dict(process=process)


class WidgetWire(WidgetMyVBox):
    heading_level = 4

    def __init__(self):
        self.diameter = FloatWithUnit("diameter", unit="mm", min=0, value=1.2)
        self.wire_class = WidgetLabeledTextInput("class", "G 42 2 C/M G4Si1")

        # TODO: consider a tree like editing widget for metadata.
        self.metadata = WidgetLabeledTextInput("metadata", "")
        children = [
            make_title("Wire parameters", heading_level=WidgetWire.heading_level),
            self.diameter,
            self.wire_class,
            self.metadata,
        ]
        super(WidgetWire, self).__init__(children=children)

    def to_tree(self):
        return {
            "diameter": self.diameter.quantity,
            "class": self.wire_class.text_value,
            # TODO:
            "wx_user": {"manufacturer": "WDI", "charge id": "00349764"},
        }


class WidgetGMAW(WidgetMyVBox, WeldxImportExport):
    translate = {
        "Spray": "spray",
        "Pulsed (UI)": "UI",
        "Pulsed (II)": "II",
        "CMT": NotImplemented,
    }

    @property
    def schema(self) -> str:
        raise

    def __init__(self):
        self.process_type = Dropdown(
            options=list(self.translate.keys()),
            index=0,
            description="Process type",
        )
        self.process_type.observe(self._create_process_widgets, names="value")
        self.gas = WidgetGasSelection()
        self.welding_process = WidgetMyVBox()
        self.welding_wire = WidgetWire()

        children = [
            make_title("GMAW process parameters"),
            self.gas,
            self.welding_wire,
            # self.weld_speed, # TODO: speed is given by feedrate and groove!
            # TODO: if no groove is given? here we dont know about the groove!
            self.process_type,
            self.welding_process,
        ]
        super(WidgetGMAW, self).__init__(children=children)

        # initially create the selected process type
        self._create_process_widgets(dict(new=self.process_type.value))

    def _create_process_widgets(self, change):
        new = change["new"]
        arg = self.translate[new]
        box = self._cached_process_widgets(arg)
        self.welding_process.children = (box,)

    @lru_cache(maxsize=3)
    def _cached_process_widgets(self, process):
        if process == "spray":
            return ProcessSpray()

        return PulsedProcess(kind=process)

    def from_tree(self, tree: dict):
        raise NotImplementedError

    def to_tree(self):
        widget_process = self.welding_process.children[0]
        welding_process = widget_process.to_tree()["process"]

        process = dict(
            welding_process=welding_process,
            shielding_gas=self.gas.to_tree()["shielding_gas"],
            weld_speed=TimeSeries(Q_(45, "cm/min")),
            welding_wire=self.welding_wire.to_tree(),
        )
        return process


@pytest.mark.parametrize("process", ["spray", "UI", "II"])
def test_create_widget_from_schema(process):
    create_widget_from_yaml(process=process)


def test_widget_gmaw():
    WidgetGMAW()
