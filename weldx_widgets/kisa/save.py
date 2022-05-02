"""Widget to save the state of a WeldxFile and invoke the next step in the pipeline."""
import pathlib
import typing
from os import environ as env
from typing import Any, Dict, Mapping, TypeVar
from urllib.parse import parse_qs, urlencode

import ipywidgets as w

import weldx
import weldx_widgets
import weldx_widgets.widget_base
import weldx_widgets.widget_factory
from weldx_widgets.translation_utils import _i18n as _
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


_KeyType = TypeVar("KeyType")


def _deep_update_inplace(
    mapping: Dict[_KeyType, Any], *updating_mappings: Dict[_KeyType, Any]
) -> Dict[_KeyType, Any]:
    for updating_mapping in updating_mappings:
        for k, v in updating_mapping.items():
            if k in mapping and isinstance(mapping[k], dict) and isinstance(v, Mapping):
                mapping[k] = _deep_update_inplace(mapping[k], v)
            else:
                mapping[k] = v
    return mapping


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
        next_notebook_desc: str = "Invoke next step",
        next_notebook_params=None,
        title="Save results",
        disable_next_button=True,
    ):
        self.status = status
        self.collect_data_from = collect_data_from
        self.out = w.Output()

        if not disable_next_button:
            self.btn_next = w.Button(
                description=_(next_notebook_desc), layout=button_layout
            )
            if next_notebook_params is None:
                next_notebook_params = dict()
            self.next_notebook_params = next_notebook_params
            self.next_notebook = next_notebook
            self.btn_next.on_click(self.on_next)

        self._initial_file = filename  # remember initial choice of file.
        fn_path = pathlib.Path(filename)
        path = str(fn_path.parent)
        fn = str(fn_path.name)
        self.save_button = weldx_widgets.WidgetSaveButton(
            desc="1." + _("Save") if not disable_next_button else _("Save"),
            filename=fn,
            path=path,
            select_default=True,
        )
        self.save_button.set_handler(self.on_save)
        if not disable_next_button:
            self.save_button.children += (self.btn_next,)

        children = [
            weldx_widgets.widget_factory.make_title(title),
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

        clear_output()

        result = dict()
        for widget in self.collect_data_from:
            _deep_update_inplace(result, widget.to_tree())

        # set status
        result["wx_user"] = {"KISA": {"status": self.status}}

        def show_header(handle):
            with self.out:
                clear_output()
                display(handle.header(False, True))

        # open (existing) file and update it.
        if pathlib.Path(self.filename).stem.endswith("_r"):
            with self.out:
                print("Refusing to save a read-only (template) file!")
                print("Please choose another name with the '_r' suffix.")
            return
        if self.filename != self._initial_file:
            # we want to save the previous file under a different name, so load contents
            with weldx.WeldxFile(self._initial_file, mode="r") as fh:
                _deep_update_inplace(fh, result)
                if not pathlib.Path(self.filename).exists():
                    fh.write_to(self.filename)
                    show_header(fh)
                else:
                    with weldx.WeldxFile(self.filename, mode="rw") as fh2:
                        _deep_update_inplace(fh2, fh)
                        show_header(fh2)
        else:
            with weldx.WeldxFile(self.filename, mode="rw", sync=True) as fh:
                _deep_update_inplace(fh, result)
                show_header(fh)

    def on_next(self, _):
        """Invoke next notebook."""
        build_url(
            board=self.next_notebook,
            parameters=dict(file=self.filename, **self.next_notebook_params),
            invoke=True,
            out=self.out,
        )
