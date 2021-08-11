import abc

from IPython.core.display import display
from ipywidgets import Output, HBox, VBox


class WidgetBase(abc.ABC):
    """Base class for weldx widgets."""

    def copy(self):
        from copy import deepcopy

        return deepcopy(self)

    def display(self):
        """initial drawing of the widget."""
        if not hasattr(self, "_ipython_display_"):
            raise NotImplementedError
        self._ipython_display_()

    def set_visible(self, state: bool):
        """toggle visibility."""
        if not hasattr(self, "layout"):
            raise NotImplementedError
        if state:
            visibility = 'visible'
        else:
            visibility = 'hidden'
        self.layout.visibility = visibility

    def _ipython_display_(self):
        self.display()


def metaclass_resolver(*classes):
    metaclass = tuple(set(type(cls) for cls in classes))
    metaclass = (
        metaclass[0]
        if len(metaclass) == 1
        else type("_".join(mcls.__name__ for mcls in metaclass), metaclass, {})
    )  # class M_C
    return metaclass("_".join(cls.__name__ for cls in classes), classes, {})  # class C


class WidgetMyHBox(metaclass_resolver(HBox, WidgetBase)):
    pass


class WidgetMyVBox(metaclass_resolver(VBox, WidgetBase)):
    pass


class WidgetSimpleOutput(WidgetMyHBox):
    def __init__(self, out=None):
        if out is None:
            from .widget_factory import layout_generic_output

            out = Output(layout=layout_generic_output)
        self.out = out
        super(WidgetSimpleOutput, self).__init__(children=[self.out])

    def __enter__(self):
        return self.out.__enter__()

    def __exit__(self, exc_type, exc_val, exc_tb):
        return self.out.__exit__(exc_type, exc_val, exc_tb)
