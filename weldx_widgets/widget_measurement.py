"""Widget to wrap around a measurement."""
from matplotlib import pylab as plt

import weldx
from weldx.constants import WELDX_UNIT_REGISTRY as ureg
from weldx_widgets.widget_base import WidgetSimpleOutput

_DEFAUL_FIGWIDTH = 10


def plot_signal(signal, name, limits=None, ax=None):
    """Plot a single weldx signal."""
    data = signal.data
    time = weldx.util.pandas_time_delta_to_quantity(data.time)

    ax.plot(time.m, data.data.m)
    ax.set_ylabel(f"{name} / {ureg.Unit(signal.unit):~}")
    ax.set_xlabel("time / s")
    ax.grid()

    if limits is not None:
        ax.set_xlim(limits)


def plot_measurements(
    measurement_data,
    axes,
    limits=None,
):
    """Plot several measurements."""
    for i, measurement in enumerate(measurement_data):
        last_signal = measurement.measurement_chain.signals[-1]
        plot_signal(last_signal, measurement.name, ax=axes[i], limits=limits)
        axes[i].set_xlabel(None)

    axes[-1].set_xlabel("time / s")
    axes[0].set_title("Measurements")


class WidgetMeasurement(WidgetSimpleOutput):
    """Widget to wrap around a measurement."""

    def __init__(self, measurement: "weldx.measurement.Measurement"):
        super(WidgetMeasurement, self).__init__()

        n = len(measurement)

        # TODO: plot m-chain?

        with self.out:
            self.fig, self.axes = plt.subplots(
                nrows=n,
                sharex="all",
                figsize=(_DEFAUL_FIGWIDTH, 2.5 * n),
            )
            plot_measurements(measurement, axes=self.axes)
