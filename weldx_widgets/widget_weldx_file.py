"""Widget to handle a WeldxFile."""
from weldx import WeldxFile

__all__ = ["WidgetWeldxFile"]


class WidgetWeldxFile:
    """Widget to handle a WeldxFile.

    this should aid:
    * the creation (filename, uri, buffer, url_parameter?)
    * visualization (header, saved objects?)
    * saving/updating

    consider a prime widget like ipytree to handle the tree like structure and
    provide useful elements within the tree (e.g. plots of U, I), CSM tree visualization

    """

    def __init__(self, wx_file: WeldxFile):
        self.file = wx_file

    def show_header(self):
        """Show ASDF header."""
        self.file.show_asdf_header()

    def display(self):
        """Show the file."""
        raise NotImplementedError
