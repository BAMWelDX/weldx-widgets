"""Widget to edit weldx.GMAW process data."""
from functools import lru_cache
from typing import Union

from bidict import bidict
from ipywidgets import Dropdown
from matplotlib import pylab as plt

from weldx import Q_, GmawProcess, Time, TimeSeries
from weldx_widgets import WidgetShieldingGas
from weldx_widgets.generic import WidgetTimeSeries
from weldx_widgets.translation_utils import _i18n as _
from weldx_widgets.widget_base import WeldxImportExport, WidgetMyVBox
from weldx_widgets.widget_factory import (
    FloatWithUnit,
    WidgetLabeledTextInput,
    make_title,
)

_DEFAULT_FIGWIDTH = 12


def parplot(par, t, name, ax):
    """Plot a single parameter into an axis."""
    ts = par.interp_time(t)
    x = Time(t).as_quantity()
    ax.plot(x.m, ts.data.m)
    ax.set_ylabel(f"{name} / {ts.data.u:~}")
    ax.grid()


def plot_gmaw(gmaw, t):
    """Plot a dictionary of parameters."""
    title = "\n".join([gmaw.manufacturer, gmaw.power_source, gmaw.base_process])

    pars = gmaw.parameters
    n = len(pars)

    fig, ax = plt.subplots(nrows=n, sharex="all", figsize=(_DEFAULT_FIGWIDTH, 2 * n))
    for i, k in enumerate(pars):
        parplot(pars[k], t, k, ax[i])
    ax[-1].set_xlabel(_("time") + " / s")
    ax[0].set_title(title, loc="left")

    # ipympl_style(fig)

    return fig, ax


def from_scalar_timeseries_to_q(ts: TimeSeries) -> Q_:
    """Create a Quantity from the given series."""
    return Q_(ts.data, ts.units)


class BaseProcess(WidgetMyVBox):
    """Widget for base process."""

    def __init__(self, tag: str, meta=None):
        self.tag = tag
        self.meta = meta

        self.manufacturer = WidgetLabeledTextInput(_("Manufacturer"), "Fronius")
        self.power_source = WidgetLabeledTextInput(_("Power source"), "TPS 500i")
        self.wire_feedrate = FloatWithUnit(
            text=_("Wire feed rate"), value=10, min=0, unit="m/min"
        )
        children = [
            self.manufacturer,
            self.power_source,
            self.wire_feedrate,
        ]
        super(BaseProcess, self).__init__(children=children)

    def to_tree(self):
        """Return base process parameters."""
        process = GmawProcess(
            base_process="not yet specified",
            manufacturer=self.manufacturer.text_value,
            power_source=self.power_source.text_value,
            parameters=dict(wire_feedrate=self.wire_feedrate.quantity),
            tag=self.tag,
            meta=self.meta,
        )
        return dict(process=process)

    def from_tree(self, tree):
        """Fill widget with tree data."""
        process: GmawProcess = tree["welding_process"]
        self.manufacturer.text_value = process.manufacturer
        self.power_source.text_value = process.power_source
        self.wire_feedrate.quantity = from_scalar_timeseries_to_q(
            process.parameters["wire_feedrate"]
        )
        self.tag = process.tag
        self.meta = process.meta


class ProcessPulsed(WidgetMyVBox):
    """Widget for pulsed processes."""

    def __init__(self, kind="UI"):
        self.pulse_duration = FloatWithUnit(_("Pulse duration"), value=5.0, unit="ms")
        self.pulse_frequency = FloatWithUnit(
            _("Pulse frequency"), value=100.0, unit="Hz"
        )
        self.base_current = FloatWithUnit(_("Base current"), value=60.0, unit="A")

        if kind == "UI":
            self.pulsed_dim = FloatWithUnit(_("Pulse voltage"), "V", 40)
        elif kind == "II":
            self.pulsed_dim = FloatWithUnit(_("Pulse current"), "A", 300)
        else:
            raise ValueError(f"unknown kind: {kind}")
        self.kind = kind
        self.base_process = BaseProcess("CLOOS/pulse", {"modulation": self.kind})

        if self.kind == "UI":
            desc = _("voltage/current")
        else:
            desc = _("current")
        children = [
            make_title(_("Pulsed") + f" {desc} " + _("process parameters")),
            self.base_process,
            self.pulse_duration,
            self.pulse_frequency,
            self.base_current,
            self.pulsed_dim,
        ]
        super(ProcessPulsed, self).__init__(children=children)

    def to_tree(self):
        """Return pulsed process parameters."""
        tree = self.base_process.to_tree()
        process = tree["process"]
        process.base_process = "pulse"

        # these params have to be quantities
        params = dict(
            pulse_duration=self.pulse_duration.quantity,
            pulse_frequency=self.pulse_frequency.quantity,
            base_current=self.base_current.quantity,
        )
        if self.kind == "UI":
            params["pulse_voltage"] = self.pulsed_dim.quantity
        else:
            params["pulse_current"] = self.pulsed_dim.quantity

        process.parameters.update(params)
        process.__post_init__()  # convert all parameters to timeseries.
        return tree

    def from_tree(self, tree):
        """Fill parameters from tree."""
        self.base_process.from_tree(tree)
        process = tree["welding_process"]
        self.kind = process.meta["modulation"]

        params = process.parameters
        self.pulse_duration.quantity = from_scalar_timeseries_to_q(
            params["pulse_duration"]
        )
        self.pulse_frequency.quantity = from_scalar_timeseries_to_q(
            params["pulse_frequency"]
        )
        self.base_current.quantity = from_scalar_timeseries_to_q(params["base_current"])

        if self.kind == "UI":
            self.pulsed_dim.quantity = from_scalar_timeseries_to_q(
                params["pulse_voltage"]
            )
        else:
            self.pulsed_dim.quantity = from_scalar_timeseries_to_q(
                params["pulse_current"]
            )


class ProcessSpray(WidgetMyVBox):
    """Widget for spray process."""

    def __init__(self):
        self.base_process = BaseProcess("CLOOS/spray_arc")
        self.voltage = WidgetTimeSeries(
            base_data="40.0, 20.0", base_unit="V", time_data="0.0, 10.0", time_unit="s"
        )
        self.impedance = FloatWithUnit(text=_("Impedance"), value=10, unit="percent")
        self.characteristic = FloatWithUnit(_("Characteristic"), value=5, unit="V/A")

        super(ProcessSpray, self).__init__(
            children=[
                make_title(_("Spray process parameters")),
                self.base_process,
                self.voltage,
                self.impedance,
                self.characteristic,
            ]
        )

    def to_tree(self):
        """Return spray process parameters."""
        tree = self.base_process.to_tree()
        process = tree["process"]
        process.base_process = "spray"
        # these params have to be quantities
        params = dict(
            voltage=self.voltage.to_tree()["timeseries"],
            impedance=self.impedance.as_time_series(),
            characteristic=self.characteristic.as_time_series(),
        )
        process.parameters.update(params)
        process.__post_init__()  # convert all parameters to timeseries.
        return tree

    def from_tree(self, tree):
        """Set widget state from tree."""
        self.base_process.from_tree(tree)
        process = tree["welding_process"]
        parameters = process.parameters

        self.voltage.from_tree(dict(timeseries=parameters["voltage"]))

        self.impedance.quantity = from_scalar_timeseries_to_q(parameters["impedance"])
        self.characteristic.quantity = from_scalar_timeseries_to_q(
            parameters["characteristic"]
        )


class WidgetWire(WidgetMyVBox):
    """Widget for welding wire."""

    heading_level = 4

    def __init__(self):
        self.diameter = FloatWithUnit(_("Diameter"), unit="mm", min=0, value=1.2)
        self.wire_class = WidgetLabeledTextInput(_("Class"), "G 42 2 C/M G4Si1")

        # TODO: consider a tree like editing widget for metadata.
        self.metadata = WidgetLabeledTextInput(_("Metadata"), "")
        children = [
            make_title(_("Wire parameters"), heading_level=WidgetWire.heading_level),
            self.diameter,
            self.wire_class,
            self.metadata,
        ]
        super(WidgetWire, self).__init__(children=children)

    def to_tree(self):
        """Return welding wire parameters."""
        return {
            "diameter": self.diameter.quantity,
            "class": self.wire_class.text_value,
            # TODO:
            "wx_user": {"manufacturer": "WDI", "charge id": "00349764"},
        }

    def from_tree(self, tree):
        """Set widget state from tree."""
        wire = tree["welding_wire"]
        self.diameter.quantity = wire["diameter"]
        self.wire_class.text_value = wire["class"]
        self.metadata.text_value = str(wire["wx_user"])


class WidgetGMAW(WidgetMyVBox, WeldxImportExport):
    """Widget to handle gas metal arc welding process parameters."""

    def _set_gui_mapping(self):
        self.translate = bidict(
            {
                _("Spray"): "spray",
                _("Pulsed") + " (UI)": "UI",
                _("Pulsed") + " (II)": "II",
                # _("CMT"): NotImplemented,
            }
        )

    @property
    def schema(self) -> str:
        """Return schema."""
        raise

    def __init__(self, process_type="spray"):
        self._set_gui_mapping()  # set up translation mapping.
        index = list(self.translate.values()).index(process_type)
        self.process_type = Dropdown(
            options=list(self.translate.keys()),
            index=index,
            description=_("Process type"),
        )
        self.process_type.observe(self._create_process_widgets, names="value")
        self.gas = WidgetShieldingGas()
        self._welding_process = WidgetMyVBox()
        self.welding_wire = WidgetWire()

        children = [
            make_title(_("GMAW process parameters")),
            make_title(_("Shielding gas"), 4),
            self.gas,
            self.welding_wire,
            # self.weld_speed, # TODO: speed is given by feedrate and groove!
            # TODO: if no groove is given? here we dont know about the groove!
            self.process_type,
            self._welding_process,
        ]
        super(WidgetGMAW, self).__init__(children=children)

        # initially create the selected process type
        self._create_process_widgets(dict(new=self.process_type.value))

    def _create_process_widgets(self, change):
        new = change["new"]
        arg = self.translate[new]
        box = self._cached_process_widgets(arg)
        self._welding_process.children = (box,)

    @property
    def welding_process(self) -> Union[ProcessSpray, ProcessPulsed]:
        """Return welding process widget."""
        return self._welding_process.children[0]

    @lru_cache(None)
    def _cached_process_widgets(self, process):
        if process == "spray":
            return ProcessSpray()

        return ProcessPulsed(kind=process)

    def from_tree(self, tree: dict):
        """Fill widget from tree."""
        process = tree["process"]
        welding_process = process["welding_process"]

        # set the right welding process widget
        if welding_process.base_process == "pulse":
            kind = welding_process.meta["modulation"]
            process_type = _("Pulsed") + f" ({kind})"
        elif welding_process.base_process == "spray":
            process_type = _("Spray")
        else:
            raise NotImplementedError(
                _("unknown process type") + f"{welding_process.base_process}"
            )
        self.process_type.value = process_type

        self.welding_process.from_tree(process)
        self.gas.from_tree(process)
        self.welding_wire.from_tree(process)

    def to_tree(self):
        """Return GMAW process parameters."""
        welding_process = self.welding_process.to_tree()["process"]

        process = dict(
            process=dict(
                welding_process=welding_process,
                shielding_gas=self.gas.to_tree()["shielding_gas"],
                # TODO: handle weld speed correctly.
                weld_speed=TimeSeries(Q_(45, "cm/min")),
                welding_wire=self.welding_wire.to_tree(),
            )
        )
        return process
