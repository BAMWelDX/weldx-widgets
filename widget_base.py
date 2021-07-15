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
    def set_visible(self, state):
        """toggle visibility."""
        pass


class WidgetSimpleOutput(WidgetBase):
    def display(self):
        display((self.out,))

    def __init__(self):
        self.out = Output()

    # FIXME: doesnt work!
    def set_visible(self, state):
        if state:
            self.out.layout.visible = True
        else:
            self.out.layout.visible = False
