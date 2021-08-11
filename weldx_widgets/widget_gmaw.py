from functools import lru_cache

import pytest
from ipywidgets import Dropdown
from matplotlib import pylab as plt

import weldx
from weldx import GmawProcess, Q_
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

    fig, ax = plt.subplots(nrows=n, sharex="all", figsize=(_DEFAUL_FIGWIDTH, 2 * n))
    for i, k in enumerate(pars):
        parplot(pars[k], t, k, ax[i])
    ax[-1].set_xlabel(f"time / s")
    ax[0].set_title(title, loc="left")

    # ipympl_style(fig)

    return fig, ax


def gmaw_procs():
    # spray arc processes
    params_spray = dict(
        wire_feedrate=Q_(10.0, "m/min"),
        voltage=TS(data=Q_([40.0, 20.0], "V"), time=Q_([0.0, 10.0], "s")),
        impedance=Q_(10.0, "percent"),
        characteristic=Q_(5, "V/A"),
    )
    process_spray = GmawProcess(
        "spray", "CLOOS", "Quinto", params_spray, tag="CLOOS/spray_arc"
    )

    # pulsed arc processes
    # U, I modulation:
    params_pulse = dict(
        wire_feedrate=Q_(10.0, "m/min"),
        pulse_voltage=Q_(40.0, "V"),
        pulse_duration=Q_(5.0, "ms"),
        pulse_frequency=Q_(100.0, "Hz"),
        base_current=Q_(60.0, "A"),
    )
    process_pulse = GmawProcess(
        "pulse",
        "CLOOS",
        "Quinto",
        params_pulse,
        tag="CLOOS/pulse",
        meta={"modulation": "UI"},
    )

    # I, I modulation
    params_pulse_II = dict(
        wire_feedrate=Q_(10.0, "m/min"),
        pulse_current=Q_(0.3, "kA"),
        pulse_duration=Q_(5.0, "ms"),
        pulse_frequency=Q_(100.0, "Hz"),
        base_current=Q_(60.0, "A"),
    )
    process_pulse_II = GmawProcess(
        "pulse",
        "CLOOS",
        "Quinto",
        params_pulse_II,
        tag="CLOOS/pulse",
        meta={"modulation": "II"},
    )


# TODO: define base process parameters
class BaseProcess:
    def __init__(self, base_process="spray"):
        # if base_process
        self.manufacturer = WidgetLabeledTextInput("Manufacturer", "Fronius")
        self.power_source = WidgetLabeledTextInput("Power source", "TPS 500i")


def create_widget_from_yaml(
    schema_pattern="process/terms*",
    process="spray",
):
    import yaml
    from weldx.asdf.util import get_schema_path

    s = get_schema_path(schema_pattern)
    with open(s) as fh:
        schema = yaml.safe_load(fh)

    w = WidgetMyVBox()
    children = [make_title(f"{process} parameters")]

    # required by process
    def get_required(proc):
        return proc["properties"]["parameters"]["required"]

    if process == "spray":
        required = get_required(schema["process"][process])
    elif process in ("UI", "II"):
        required = get_required(schema["process"]["pulse"][process])
    else:
        raise ValueError("unknown process", process)

    params = schema["parameters"]
    widget_by_param_name = {}
    for k, v in params.items():
        if not "time_series" in v["tag"]:
            raise NotImplementedError("handles time series tag only atm.")

        if k not in required:
            continue
        label_text = f"{k[0].upper()}{k[1:].replace('_', ' ')}"
        wx_unit = v["wx_unit"]
        tooltip = v["description"]
        # TODO: it would be nice to know, if a TS is meant to be a scalar or really time-dependent.
        w_child = WidgetTimeSeries(time_unit="s", base_unit=wx_unit, title=label_text)
        w.tooltip = tooltip
        children.append(w_child)
        widget_by_param_name[k] = w_child

    w.children = children
    w.params = widget_by_param_name
    return w


class ProcessSpray(WidgetMyVBox):
    def __init__(self):
        self.wire_feedrate = FloatWithUnit(
            text="Wire feedrate", value=10, min=0, unit="m/min"
        )
        self.voltage = WidgetTimeSeries(
            base_data="40.0, 20.0", base_unit="V", time_data="0.0, 10.0", time_unit="s"
        )
        self.impedance = FloatWithUnit(text="Impendance", value=10, unit="percent")
        self.characteristic = FloatWithUnit("characteristic", value=5, unit="V/A")

        super(ProcessSpray, self).__init__(
            children=[
                make_title("Spray process parameters"),
                self.wire_feedrate,
                self.voltage,
                self.impedance,
                self.characteristic,
            ]
        )


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
            "diameter": Q_(self.diameter.float_value, self.diameter.unit),
            "class": self.wire_class.text_value,
            # TODO:
            "wx_user": {"manufacturer": "WDI", "charge id": "00349764"},
        }


class WidgetGMAW(WidgetMyVBox, WeldxImportExport):
    @property
    def schema(self) -> str:
        raise

    def __init__(self):
        self.process_type = Dropdown(
            options=[
                "Spray",
                "Pulsed (UI)",
                "Pulsed (II)",
                "CMT",
            ],
            index=0,
            description="Process type",
            # layout=
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
            self.
            # TODO: if no groove is given?
            self.process_type,
            self.welding_process,
        ]
        super(WidgetGMAW, self).__init__(children=children)

        # initially create the selected process type
        self._create_process_widgets(dict(new=self.process_type.value))

    def _create_process_widgets(self, change):
        new = change["new"]
        translate = {
            "Spray": "spray",
            "Pulsed (UI)": "UI",
            "Pulsed (II)": "II",
            "CMT": NotImplemented,
        }
        arg = translate[new]
        box = self._cached_process_widgets(arg)
        self.welding_process.children = (box,)

    @lru_cache(maxsize=4)
    def _cached_process_widgets(self, process):
        return create_widget_from_yaml(process=process)

    def to_tree(self):
        return dict(
            process=dict(
                welding_wire=self.welding_wire.to_tree(),
                welding_speed=self.welding_speed.to,
                welding_process=self.welding_process.to_tree(),
                shielding_gas=self.gas.to_tree(),
            )
        )

    def from_tree(self, tree: dict):
        pass


@pytest.mark.parametrize("process", ["spray", "UI", "II"])
def test_create_widget_from_schema(process):
    create_widget_from_yaml(process=process)


def test_widget_gmaw():
    WidgetGMAW()
