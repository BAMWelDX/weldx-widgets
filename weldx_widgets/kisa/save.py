"""Widget to save the state of a WeldxFile and invoke the next step in the pipeline."""
import pathlib
import typing
from os import environ as env
from urllib.parse import parse_qs, urlencode

import ipywidgets as w

import weldx
import weldx_widgets
import weldx_widgets.widget_base
import weldx_widgets.widget_factory
from weldx_widgets.widget_factory import button_layout

__all__ = [
    "SaveAndNext",
    "build_url",
    "get_param_from_env",
    "invoke_url",
]


def get_param_from_env(name, default=None) -> str:
    """Extract parameter from env.QUERY_STRING.

    Parameters
    ----------
    name :
        name of the parameter to extract.

    default :
        optional default value, if parameter is not set.

    Returns
    -------
    str :
        value of the requested parameter.

    """
    query_string = env.get("QUERY_STRING", "")
    parameters = parse_qs(query_string)
    try:
        value = parameters[name][0]
    except KeyError:  # TODO: this can also raise something else, right?
        if default:
            return default
        else:
            raise RuntimeError(
                f"parameter '{name}' unset and no default provided."
                f" Given parameters: {parameters}"
            )
    return value


def build_url(board: str, parameters: dict = None, invoke=True, out=None) -> str:
    """Build an URL with given parameters.

    Parameters
    ----------
    board :
        dash board to invoke next. May contain a relative path.
    parameters :
        optional parameters to encode.
    invoke :
        should the url be invoked in a web browser?

    Returns
    -------
    str :
        the built url.
    """
    if invoke and not out:
        raise ValueError("need output to invoke Javascript.")

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
        url += f"?{params_encoded}"

    if invoke:
        invoke_url(url, out)
    return url


def invoke_url(url, out):
    """Invoke url in new browser tab.

    We cannot use python stdlib webbrowser here, because this code will be executed
    on the server. So we impl this via Javascript.
    """
    from IPython.display import Javascript, clear_output, display

    with out:
        clear_output()
        js = Javascript(f'window.open("{url}");')
        display(js)


class SaveAndNext(weldx_widgets.widget_base.WidgetMyVBox):
    """Collect all the data from passed import/output widget list and stores it.

    Parameters
    ----------
    filename:
        output file name.
    next_notebook:
        next dashboard/notebook to invoke.
    status :
        the file update will contain the new status.
    collect_data_from :
        a list of widgets to build a tree from.
    next_notebook_params :
        optional parameters for next dashboard.

    Notes
    -----
    The passed status will be set into the wx_user["kisa"]["status"] dict.
    """

    def __init__(
        self,
        filename,
        next_notebook: str,
        status: str,
        collect_data_from: typing.List[weldx_widgets.widget_base.WeldxImportExport],
        next_notebook_desc: str = "2. invoke next step",
        next_notebook_params=None,
    ):
        self.status = status
        self.collect_data_from = collect_data_from
        self.out = w.Output()

        self.btn_next = w.Button(description=next_notebook_desc, layout=button_layout)
        if next_notebook_params is None:
            next_notebook_params = dict()
        self.next_notebook_params = next_notebook_params
        self.next_notebook = next_notebook
        self.btn_next.on_click(self.on_next)

        fn_path = pathlib.Path(filename)
        path = str(fn_path.parent)
        fn = str(fn_path.name)
        self.save_button = weldx_widgets.WidgetSaveButton(
            desc="1. Save", filename=fn, path=path
        )
        self.save_button.button.on_click(self.on_save)
        self.save_button.children += (self.btn_next,)

        children = [
            weldx_widgets.widget_factory.make_title("Save results"),
            self.save_button,
            self.out,
        ]
        super(SaveAndNext, self).__init__(children=children)

    @property
    def filename(self):
        """Return output file name."""
        return self.save_button.path

    def on_save(self, _):
        """Handle saving data to file."""
        from IPython.display import clear_output, display

        # TODO: error handling, e.g. to_tree() is not yet ready etc.
        result = dict()
        for widget in self.collect_data_from:
            result.update(widget.to_tree())
        result["wx_user"] = {"KISA": {"status": self.status}}
        assert self.filename
        # open (existing) file and update it.
        clear_output()
        with weldx.WeldxFile(self.filename, mode="rw", sync=True) as fh, self.out:
            fh.update(**result)
            display(fh)

    def on_next(self, _):
        """Invoke next notebook."""
        build_url(
            board=self.next_notebook,
            parameters=dict(file=self.filename, **self.next_notebook_params),
            invoke=True,
            out=self.out,
        )


def test_on_save(tmpdir):
    """Ensure data from input widget get serialized to desired output file."""

    class simple_export:
        def to_tree(self):
            return {"data": 42}

    out_file = str(tmpdir / "out")
    status = "test"
    w = SaveAndNext(
        out_file, next_notebook="no", collect_data_from=[simple_export()], status=status
    )
    w.on_save(None)
    # verify output
    with weldx.WeldxFile(out_file) as wx:
        assert wx["data"] == 42
        assert wx["wx_user"]["KISA"]["status"] == status
