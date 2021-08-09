from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("package-name")
except PackageNotFoundError:
    # package is not installed
    pass

from widget_scans import WidgetScans
from widget_groove_sel import WidgetGrooveSelection, WidgetGrooveSelectionTCPMovement


__all__ = [
    "WidgetScans",
    "WidgetGrooveSelection",
    "WidgetGrooveSelectionTCPMovement",
]
