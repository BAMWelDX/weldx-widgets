import ipywidgets as w
from weldx import GmawProcess, Q_

from weldx_widgets.generic import WidgetTimeSeries
from weldx_widgets.widget_base import WidgetMyHBox
from matplotlib import pylab as plt
import weldx

from weldx_widgets.widget_factory import description_layout, FloatWithUnit, make_title


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


def demo_process():
    process = dict(
        welding_process=process_pulse,
        shielding_gas=gas_for_procedure,
        weld_speed=TimeSeries(v_weld),
        welding_wire={"diameter": Q_(1.2, "mm")},
    )


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


class ProcessSpray(WidgetMyHBox):
    def __init__(self):
        self.wire_feedrate = (
            FloatWithUnit(text="Wire feedrate", value=10, unit="m/min"),
        )
        self.voltage = WidgetTimeSeries(
            data=Q_([40.0, 20.0], "V"), time=Q_([0.0, 10.0], "s")
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


class ProcessPulse:
    pass


"""
class GmawProcess:
  Container class for all GMAW processes.

    base_process: str
    manufacturer: str
    power_source: str
    parameters: Dict[str, TimeSeries]
    tag: str = None
    meta: dict = None
    """


class WidgetGMAW(WidgetMyHBox):
    def __init__(self):
        # drahtvorschub     wx_unit: "m/s"

        super(WidgetGMAW, self).__init__()

        # choose between pulse or spray
        spray = w.Checkbox(desc="foo", layout=description_layout)
        self.box = w.HBox([spray])

    def display(self):
        from IPython.core.display import display

        display(self.box)
