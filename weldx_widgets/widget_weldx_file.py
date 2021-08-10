from weldx import WeldxFile
from weldx.types import types_path_and_file_like


class WidgetWeldxFile:
    """

    this should aid:
    * the creation (filename, uri, buffer, url_parameter?)
    * visualization (header, saved objects?)
    * saving/updating
    *

    """

    def __init__(self, fn: types_path_and_file_like = None):
        self.file = WeldxFile(fn)

    def save(self):
        pass

    def sync(self):
        pass

    def show_header(self):
        pass

    def display(self):
        pass
