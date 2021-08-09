from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("package-name")
except PackageNotFoundError:
    # package is not installed
    pass

from .generic import WidgetSaveButton
from .widget_scans import WidgetScans
from .widget_groove_sel import WidgetGrooveSelection, WidgetGrooveSelectionTCPMovement
from .widget_gas import WidgetGasSelection

__all__ = [
    WidgetScans,
    WidgetGrooveSelection,
    WidgetGrooveSelectionTCPMovement,
    WidgetGasSelection,
]
__all__ = map(str, __all__)
