"""Widget to wrap around a measurement."""
from typing import List

from matplotlib import pylab as plt

import weldx
from weldx.constants import WELDX_UNIT_REGISTRY as ureg
from weldx_widgets.translation_utils import _i18n as _
from weldx_widgets.widget_base import WidgetSimpleOutput
from weldx_widgets.widget_factory import make_title

_DEFAULT_FIGWIDTH = 10


def ipympl_style(fig, toolbar=True):
    """Apply default figure styling for ipympl backend."""
    try:
        fig.canvas.header_visible = False
        fig.canvas.resizable = False
        fig.tight_layout()
        fig.canvas.toolbar_position = "right"
        fig.canvas.toolbar_visible = toolbar
    except Exception:
        pass


def plot_signal(signal: weldx.measurement.Signal, name, limits=None, ax=None):
    """Plot a single weldx signal."""
    if not ax:
        fig, ax = plt.subplots(figsize=(_DEFAULT_FIGWIDTH, 6))

    data = signal.data
    time = weldx.Time(data.time).as_quantity()

    ax.plot(time.m, data.data.m)
    ax.set_ylabel(f"{name} / {ureg.Unit(signal.units):~}")
    ax.set_xlabel(_("time") + " / s")
    ax.grid()

    if limits is not None:
        ax.set_xlim(limits)

    ipympl_style(ax.figure)


def plot_measurements(
    measurement_data,
    axes,
    limits=None,
):
    """Plot several measurements sharing time axis."""
    for i, measurement in enumerate(measurement_data):
        last_signal = measurement.measurement_chain.signals[-1]
        plot_signal(last_signal, measurement.name, ax=axes[i], limits=limits)
        axes[i].set_xlabel(None)

    axes[-1].set_xlabel(_("time") + " / s")
    axes[0].set_title(_("Measurements"))
    return axes


class WidgetMeasurement(WidgetSimpleOutput):
    """Widget to wrap around a measurement."""

    def __init__(self, measurements: List["weldx.measurement.Measurement"], out=None):
        super(WidgetMeasurement, self).__init__(out=out)

        n = len(measurements)

        with self:
            self.fig, self.axes = plt.subplots(
                nrows=n,
                sharex="all",
                figsize=(_DEFAULT_FIGWIDTH, 2.5 * n),
            )
            plot_measurements(measurements, axes=self.axes)
            ipympl_style(self.fig)
            self.fig.tight_layout()
            plt.show()


class WidgetMeasurementChain(WidgetSimpleOutput):
    """Plot measurement chains into output widget."""

    def __init__(self, measurements, out=None):
        super(WidgetMeasurementChain, self).__init__(out=out)
        with self:
            fig, ax = plt.subplots(
                nrows=len(measurements), figsize=(_DEFAULT_FIGWIDTH, 18)
            )
            for i, measurement in enumerate(measurements):
                measurement.measurement_chain.plot(ax[i])
            plt.tight_layout()
            plt.show()

        self.children = [make_title(_("Measurement chain")), self.out]
