import typing

import ipywidgets as w
from util import invoke_next_notebook

import weldx_widgets
import weldx_widgets.widget_base
import weldx_widgets.widget_factory

import weldx

from weldx_widgets.widget_base import WidgetSimpleOutput

from urllib.parse import parse_qs, urlencode
import os


def get_param_from_env(name=None, default=None) -> str:
    query_string = os.environ.get("QUERY_STRING", "")
    parameters = parse_qs(query_string)
    if not name:
        name = "wid"
    try:
        wid = parameters[name][0]
    except KeyError:
        if default:
            return default
        else:
            raise RuntimeError(
                f"parameter '{name}' unset and no default provided."
                f" Given parameters: {parameters}"
            )
    return wid


def build_url(board: str, parameters: dict = None, invoke=True) -> str:
    env = os.environ
    server = env.get("SERVER_NAME", "localhost")
    protocol = env.get("SERVER_PROTOCOL", "HTTP")
    if "HTTPS" in protocol:
        url = "https://"
    else:
        url = "http://"
    url += server

    # TODO: this only works from voila!
    port = env.get("SERVER_PORT", "8888")

    if port:
        url += f":{port}/"
    else:
        url += "/"
    voila = "voila" in env.get("SERVER_SOFTWARE", "")
    prefix = "voila/render" if voila else ""

    url += f"{prefix}/{board}"

    if parameters:
        params_encoded = urlencode(parameters)
        #print("params encoded", params_encoded)
        url += f"?{params_encoded}"

    if invoke:
        invoke_next_notebook(url)
    return url


def invoke_next_notebook(notebook, params=''):
    import webbrowser
    from urllib import parse

    params_ = parse.urlencode(params)

    webbrowser.open_new_tab(f"http://{server}:{port}/voila/render/{notebook}?{params_}")


class SaveAndNext(weldx_widgets.widget_base.WidgetMyVBox):
    """collects all the data from passed import/output widget list and stores it

    The passed status will be set into the wx_user["kisa"]["status"] dict.
    """

    def __init__(self, filename,
                 next_notebook: str,
                 status: str,
                 collect_data_from: typing.List[
                     weldx_widgets.widget_base.WeldxImportExport],
                 next_notebook_desc: str = "invoke next step",
                 ):
        self.status = status
        self.collect_data_from = collect_data_from
        self.out = WidgetSimpleOutput()

        btn_next = w.Button(description=next_notebook_desc)
        btn_next.on_click(lambda _: (invoke_next_notebook(
            next_notebook, params=dict(file=str(filename)))
        )
                          )
        self.save_button = weldx_widgets.WidgetSaveButton(self.filename, )
        self.save_button.button.on_click = self.on_save
        self.filename = filename

        children = [weldx_widgets.widget_factory.make_title("Save results"),
                    self.save_button,
                    self.out,
                    w.HTML("<hr>"),
                    self.btn_next]
        super(SaveAndNext, self).__init__(children=children)

    @property
    def filename(self):
        return self.save_button.path

    @filename.setter
    def filename(self, value):
        self.save_button.path = value

    def on_save(self, *args, **kwargs):
        # TODO: error handling, e.g. to_tree() is not yet ready etc.
        result = dict()
        for widget in self.collect_data_from:
            result.update(widget.to_tree())
        result["wx_user"] = {
            "KISA": {"status": self.status}
        }
        with weldx.WeldxFile(self.filename, tree=result, mode="rw") as fh, self.out:
            fh.show_asdf_header(True)
