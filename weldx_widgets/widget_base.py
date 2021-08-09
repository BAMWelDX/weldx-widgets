import abc

from IPython.core.display import display
from ipywidgets import Output, HBox, VBox


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
            from .widget_factory import layout_generic_output

            out = Output(layout=layout_generic_output)
        self.out = out
        super(WidgetSimpleOutput, self).__init__(children=[self.out])

    def set_visible(self, state: bool):
        # FIXME: doesnt work!
        self.out.layout.visible = bool(state)


def metaclass_resolver(*classes):
    metaclass = tuple(set(type(cls) for cls in classes))
    metaclass = (
        metaclass[0]
        if len(metaclass) == 1
        else type("_".join(mcls.__name__ for mcls in metaclass), metaclass, {})
    )  # class M_C
    return metaclass("_".join(cls.__name__ for cls in classes), classes, {})  # class C


class WidgetMyHBox(metaclass_resolver(HBox, WidgetBase)):
    def display(self):
        super(WidgetMyHBox, self).display()

    def set_visible(self):
        self.layout.visible = False


class WidgetMyVBox(metaclass_resolver(VBox, WidgetBase)):
    def display(self):
        super(WidgetMyVBox, self).display()

    def set_visible(self):
        self.layout.visible = False
