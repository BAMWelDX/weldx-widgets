"""Weldx widgets."""
from .generic import WidgetSaveButton, WidgetTimeSeries
from .widget_factory import WidgetFloatWithUnit, WidgetLabeledTextInput
from .widget_gas import WidgetShieldingGas
from .widget_gmaw import WidgetGMAW
from .widget_groove_sel import WidgetGrooveSelection, WidgetGrooveSelectionTCPMovement

__all__ = [
    WidgetGrooveSelection,
    WidgetGrooveSelectionTCPMovement,
    WidgetShieldingGas,
    WidgetTimeSeries,
    WidgetLabeledTextInput,
    WidgetSaveButton,
    WidgetGMAW,
    WidgetFloatWithUnit,
]
__all__ = map(str, (x.__name__ for x in __all__))

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("weldx_widgets")
except PackageNotFoundError:
    # package is not installed
    __version__ = "unknown(pkg-not-installed)"
finally:
    del version, PackageNotFoundError
