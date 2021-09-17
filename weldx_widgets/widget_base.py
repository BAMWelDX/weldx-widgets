"""Base classes for widgets."""
import abc
import functools
from pathlib import Path

from ipywidgets import HBox, Layout, Output, VBox

from weldx.asdf.util import get_schema_path


class WidgetBase(abc.ABC):
    """Base class for weldx widgets."""

    def copy(self):
        """Copy the widget."""
        from copy import deepcopy

        return deepcopy(self)

    def display(self):
        """Draw the widget in the frontend."""
        if not hasattr(self, "_ipython_display_"):
            raise NotImplementedError
        self._ipython_display_()

    def set_visible(self, state: bool):
        """Toggle visibility."""
        if not hasattr(self, "layout"):
            raise NotImplementedError
        if state:
            visibility = "visible"
        else:
            visibility = "hidden"
        self.layout.visibility = visibility

    def _ipython_display_(self):
        self.display()


def metaclass_resolver(*classes):
    """Merge multiple meta classes."""
    metaclass = tuple(set(type(cls) for cls in classes))
    metaclass = (
        metaclass[0]
        if len(metaclass) == 1
        else type("_".join(mcls.__name__ for mcls in metaclass), metaclass, {})
    )  # class M_C
    return metaclass("_".join(cls.__name__ for cls in classes), classes, {})  # class C


border_debug_style = ""  # 2px dashed green"
margin = ""  # "10px"


class WidgetMyHBox(metaclass_resolver(HBox, WidgetBase)):
    """Wrap around a HBox sharing a common layout."""

    def __init__(self, *args, **kwargs):
        if "layout" in kwargs:
            layout = kwargs["layout"]
        else:
            layout = Layout()
            kwargs["layout"] = layout
        layout.border = border_debug_style
        layout.margin = margin

        super(WidgetMyHBox, self).__init__(*args, **kwargs)


class WidgetMyVBox(metaclass_resolver(VBox, WidgetBase)):
    """Wrap around a VBox sharing a common layout."""

    def __init__(self, *args, **kwargs):
        if "layout" in kwargs:
            layout = kwargs["layout"]
        else:
            layout = Layout()
            kwargs["layout"] = layout
        layout.border = border_debug_style
        layout.margin = margin

        super(WidgetMyVBox, self).__init__(*args, **kwargs)


class WidgetSimpleOutput(WidgetMyHBox):
    """Wrap around a ipywidgets.Output."""

    def __init__(self, out=None, height=None, width=None):
        if out is None:
            from .widget_factory import copy_layout, layout_generic_output

            if height or width:
                layout = copy_layout(layout_generic_output)
                if height:
                    layout.height = height
                if width:
                    layout.width = width
            else:
                layout = layout_generic_output
            out = Output(layout=layout)
        self.out = out
        super(WidgetSimpleOutput, self).__init__(children=[self.out], layout=layout)

    def __enter__(self):
        """Enter."""
        return self.out.__enter__()

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit."""
        return self.out.__exit__(exc_type, exc_val, exc_tb)


class WeldxImportExport(abc.ABC):
    """Abstract import and export interfaces for weldx data exchange."""

    @property
    @abc.abstractmethod
    def schema(self) -> str:
        """Return a schema name is used to validate input and output."""
        pass

    @functools.lru_cache
    def get_schema_path(self) -> Path:
        """Resolve a schema name to path."""
        return get_schema_path(self.schema)

    def validate(self, tree):
        """Validate given tree against schema of this class."""
        # should be implemented such that we can validate both input and output.
        pass

    @abc.abstractmethod
    def from_tree(self, tree: dict):
        """Fill the widget with given state dictionary."""
        pass

    @abc.abstractmethod
    def to_tree(self) -> dict:
        """Return a dict containing data from widget."""
        pass
