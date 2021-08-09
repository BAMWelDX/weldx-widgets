from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("package-name")
except PackageNotFoundError:
    # package is not installed
    pass

from .generic import WidgetSaveButton
from .widget_scans import WidgetScans
from .widget_groove_sel import WidgetGrooveSelection, WidgetGrooveSelectionTCPMovement
from .widget_gas import WidgetGasSelection, WidgetSimpleGasSelection

__all__ = [
    WidgetScans,
    WidgetGrooveSelection,
    WidgetGrooveSelectionTCPMovement,
    WidgetGasSelection,
    WidgetSimpleGasSelection,
]
__all__ = map(str, (x.__name__ for x in __all__))
