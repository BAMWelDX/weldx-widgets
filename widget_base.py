import abc

from IPython.core.display import display
from ipywidgets import Output


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


class WidgetSimpleOutput(WidgetBase):
    def display(self):
        display((self.out,))

    def __init__(self, out=None):
        if out is None:
            out = Output()
        self.out = out

    def set_visible(self, state: bool):
        # FIXME: doesnt work!
        self.out.layout.visible = bool(state)
