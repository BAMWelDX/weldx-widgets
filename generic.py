import contextlib
from functools import partial

from IPython import get_ipython

from widget_base import WidgetSimpleOutput
import ipywidgets as w
from ipyfilechooser import FileChooser


@contextlib.contextmanager
def show_only_exception_message():
    ip = get_ipython()
    old_state = ip.showtraceback
    f = ip.showtraceback
    tb = partial(f, exception_only=True)
    ip.showtraceback = tb

    yield

    ip.showtraceback = old_state


# TODO: allow save and load with a switch!
class WidgetSaveButton(WidgetSimpleOutput):
    def __init__(self, desc="Save to", filename="out.txt", path=None):
        super(WidgetSaveButton, self).__init__()

        with self.out:
            self.file_chooser = FileChooser(path=path, filename=filename)
            self.button = w.Button(desc=desc)

        self.file_chooser.observe(self._chose_file, "selected_file") # TODO: or value?

    def _chose_file(self):
        # TODO: pre-validate the path, e.g. writeable.
        pass

    @property
    def desc(self):
        return self.button.desc

    @desc.setter
    def desc(self, value):
        self.button.desc = value

    @property
    def path(self):
        return self.file_chooser.selected_path

    @path.setter
    def path(self, value):
        self.file_chooser.default_path = value


