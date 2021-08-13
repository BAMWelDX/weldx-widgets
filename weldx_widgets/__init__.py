from .widget_factory import WidgetLabeledTextInput, FloatWithUnit
from .generic import WidgetSaveButton, WidgetTimeSeries
from .widget_scans import WidgetScans
from .widget_groove_sel import WidgetGrooveSelection, WidgetGrooveSelectionTCPMovement
from .widget_gas import WidgetGasSelection, WidgetSimpleGasSelection
from .widget_gmaw import WidgetGMAW

__all__ = [
    WidgetScans,
    WidgetGrooveSelection,
    WidgetGrooveSelectionTCPMovement,
    WidgetGasSelection,
    WidgetSimpleGasSelection,
    WidgetTimeSeries,
    WidgetLabeledTextInput,
    WidgetSaveButton,
    WidgetGMAW,
    FloatWithUnit,  # TODO: rename
]
__all__ = map(str, (x.__name__ for x in __all__))

from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("package-name")
except PackageNotFoundError:
    # package is not installed
    pass
finally:
    del version, PackageNotFoundError
