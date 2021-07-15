from widget_base import WidgetSimpleOutput
from matplotlib import pylab as plt
import weldx


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

    #ipympl_style(fig)

    return fig, ax


class GMAW_Widget(WidgetSimpleOutput):
    def __init__(self, gmaw):
        super(GMAW_Widget, self).__init__()

        with self.out:
            plot_gmaw(
                gmaw,
            )
