import abc

from IPython.core.display import display
from ipywidgets import Output

from .widget_factory import layout_generic_output


class WidgetBase(abc.ABC):
    """Base class for weldx widgets."""

    def copy(self):
        from copy import deepcopy

        return deepcopy(self)

    @abc.abstractmethod
    def display(self):
        """initial drawing of the widget."""
        pass

    @abc.abstractmethod
    def set_visible(self, state: bool):
        """toggle visibility."""

    def _ipython_display_(self):
        self.display()


# TODO: preferably we should derive some ipywidgets container...
class WidgetSimpleOutput(WidgetBase):
    def display(self):
        display(*(self.out,))

    def __init__(self, out=None):
        if out is None:
            out = Output(layout=layout_generic_output)
        self.out = out
        super(WidgetSimpleOutput, self).__init__()

    def set_visible(self, state: bool):
        # FIXME: doesnt work!
        self.out.layout.visible = bool(state)
