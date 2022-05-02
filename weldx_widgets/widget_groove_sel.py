"""Widgets to select groove type and tcp movement."""
from __future__ import annotations

import contextlib
import re
import tempfile
from typing import TYPE_CHECKING, Callable, Optional, Union

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from IPython import get_ipython
from IPython.display import display
from ipywidgets import HTML, Button, Dropdown, HBox, Label, Layout, Output, Tab

import weldx
from weldx import Geometry, SpatialData
from weldx.constants import WELDX_QUANTITY as Q_
from weldx.welding.groove.iso_9692_1 import (
    IsoBaseGroove,
    _groove_name_to_type,
    _groove_type_to_name,
    get_groove,
)
from weldx_widgets.generic import download_button
from weldx_widgets.translation_utils import _i18n as _
from weldx_widgets.widget_base import WeldxImportExport, WidgetMyHBox, WidgetMyVBox
from weldx_widgets.widget_factory import (
    FloatWithUnit,
    WidgetLabeledTextInput,
    description_layout,
    make_title,
    textbox_layout,
)

if TYPE_CHECKING:
    from weldx_widgets.visualization import CoordinateSystemManagerVisualizerK3D

__all__ = [
    "WidgetGrooveSelection",
    "WidgetGrooveSelectionTCPMovement",
]


class WidgetCADExport(WidgetMyVBox):
    """Exports SpatialData to selected CAD format.

    Attributes
    ----------
    geometry :
        `weldx.Geometry` or `weldx.SpatialData` to export. If not set, the save button
        does nothing.
    """

    data_formats = (
        [  # ".stl", # FIXME: for some reason there is a div by zero error in meshio
            ".ply"
        ]
    )  # same groove is fine in ply format...
    """ example trace for a simple vgroove:
    meshio/stl/_stl.py in write(filename, mesh, binary)
    203         normals = np.cross(pts[:, 1] - pts[:, 0], pts[:, 2] - pts[:, 0])
    204         nrm = np.sqrt(np.einsum("ij,ij->i", normals, normals))
--> 205         normals = (normals.T / nrm).T
    206
    207     fun = _write_binary if binary else _write_ascii

RuntimeWarning: invalid value encountered in true_divide
    """

    def __init__(self):
        title = make_title(_("Export geometry to CAD file [optional]"), heading_level=4)

        # if the format changes, we have to update the file_pattern mask
        # of the chooser of the save widget.
        default_format_index = 0
        self.format = Dropdown(
            options=WidgetCADExport.data_formats,
            index=default_format_index,
            description=_("Data format"),
        )
        self.create_btn = Button(description=_("Create program"))
        self.geometry = None
        # disable button initially, because we first need to have a geometry
        self.create_btn.disabled = True
        # observe here, because "btn.disabled = True" already triggers an event.
        self.create_btn.on_click(self._on_export_geometry)
        # this dynamically created button allows the user to download the
        # program directly to his/her computer.
        self._html_dl_button = HTML()

        self.profile_raster_width = FloatWithUnit(
            _("Profile raster width"),
            value=2,
            unit="mm",
            # tooltip="Target distance between the individual points of a profile",
        )
        self.trace_raster_width = FloatWithUnit(
            _("Trace raster width"),
            value=30,
            unit="mm",
            # tooltip="Target distance between the individual profiles on the trace",
        )

        children = [
            title,
            self.profile_raster_width,
            self.trace_raster_width,
            self.format,
            self.create_btn,
            self._html_dl_button,
        ]
        super().__init__(children=children)
        self.layout.border = "1px solid gray"

    @property
    def geometry(self) -> Union[SpatialData, Geometry]:
        return self._geometry

    @geometry.setter
    def geometry(self, value):
        self._geometry = value
        if value is not None:
            self.create_btn.disabled = False

    def _on_export_geometry(self, *args):
        if self.geometry is None:
            return
        ext = self.format.value
        # need to write to a file, because Geometry.write_to does not
        # expose the format parameter.
        with tempfile.NamedTemporaryFile(mode="w+b", suffix=ext) as ntf:
            if isinstance(self.geometry, Geometry):
                self.geometry.to_file(
                    ntf.name,
                    self.profile_raster_width.quantity,
                    self.trace_raster_width.quantity,
                )
            elif isinstance(self.geometry, SpatialData):  # already rasterized
                self.geometry.to_file(ntf.name)
            else:
                raise RuntimeError(f"invalid geometry type {type(self.geometry)}")
            # read and embed in HTML button.
            ntf.seek(0)
            download_button(
                button_description=_("Download program"),
                filename=f"specimen{ext}",
                html_instance=self._html_dl_button,
                content=ntf.read(),
            )


class WidgetMetal(WidgetMyVBox):
    """Widget to select metal type and parameters."""

    def __init__(self):
        self.common_name = WidgetLabeledTextInput(_("Common name"), "S355J2+N")
        self.standard = WidgetLabeledTextInput(_("Standard"), "DIN EN 10225-2:2011")
        self.thickness = FloatWithUnit(_("Thickness"), value=30, unit="mm")
        children = [
            make_title(_("Base metal"), heading_level=4),
            self.common_name,
            self.standard,
            self.thickness,
        ]
        super().__init__(children=children)

    def to_tree(self):
        """Return metal parameters."""
        return dict(
            base_metal=dict(
                common_name=self.common_name.text_value,
                standard=self.standard.text_value,
                thickness=self.thickness.quantity,
            )
        )

    def from_tree(self, tree: dict):
        base_metal = tree["base_metal"]
        self.common_name.text_value = base_metal["common_name"]
        self.standard.text_value = base_metal["standard"]
        self.thickness.quantity = base_metal["thickness"]


def get_ff_grove_code_numbers():
    """Return FFGroove code numbers."""
    return [
        "1.12",
        "1.13",
        "2.12",
        "3.1.1",
        "3.1.2",
        "3.1.3",
        "4.1.1",
        "4.1.2",
        "4.1.3",
    ]


# TODO: nice group layout for all widgets
# TODO: reset button parameters (defaults).
class WidgetGrooveSelection(WidgetMyVBox, WeldxImportExport):
    """Widget to select groove type."""

    def __init__(self):
        self._groove_obj = None

        self.out = Output()  # layout=Layout(width="100%"))
        self.groove_params_dropdowns = None

        # create figure for groove visualization
        self._create_plot()

        self.groove_params = WidgetMyVBox([])
        self.groove_type_dropdown = self._create_groove_dropdown()
        self._groove_obj_cache = {}  # store ISOBaseGroove objects mapped to type.

        self.groove_selection = WidgetMyVBox(
            [
                WidgetMyHBox(
                    [
                        Label(_("Groove type"), layout=description_layout),
                        self.groove_type_dropdown,
                    ]
                ),
                self.groove_params,
                WidgetMyVBox([]),  # additional parameters (e.g. weld speed).
            ]
        )
        # left box with parameter should be small to leave more space for plots.
        self.groove_selection.layout.width = "30%"
        self.output_tabs = Tab()
        self.output_tabs.layout = Layout(width="70%")
        self.output_tabs.children = [self.out]
        self.output_tabs.set_title(0, "2D " + _("profile"))
        children = [
            make_title(_("ISO 9692-1 Groove selection"), 3),
            WidgetMyHBox(children=[self.groove_selection, self.output_tabs]),
        ]

        # set initial state
        self._update_params_to_selection(dict(new=self.groove_type_dropdown.value))
        self._update_plot()
        super().__init__(children=children, layout=Layout(width="100%"))

    @property
    def groove_obj(self) -> IsoBaseGroove:
        """Get current groove object."""
        return self._groove_obj

    @groove_obj.setter
    def groove_obj(self, value: IsoBaseGroove):
        self._groove_obj = value

        self.groove_selection.children[0].value = _groove_type_to_name[
            self.groove_obj.__class__
        ]
        # update fields according to data in new groove object.
        gui_params = self.groove_params_dropdowns

        # inhibit notifications during updating the parameters (or we would call the
        # _update_plot method for every setting!
        with contextlib.ExitStack() as stack:
            for k, v in self.groove_obj.parameters().items():
                mapped_k = self._groove_obj._mapping[k]
                widget: FloatWithUnit = gui_params[mapped_k]
                stack.enter_context(widget.silence_events())

                widget.quantity = v

    @property
    def schema(self) -> str:
        """Return schema."""
        raise NotImplementedError

    def from_tree(self, tree: dict):
        """Fill widget from tree."""
        self.groove_obj = tree["groove_shape"]

    def to_tree(self) -> dict:
        """Return groove parameters."""
        return dict(groove_shape=self.groove_obj)

    def _create_plot(self):
        # ensure we have the proper matplotlib backend.
        ip = get_ipython()
        if ip:
            ip.run_line_magic("matplotlib", "widget")

        # TODO: fig size should match size of self.out see
        #  https://stackoverflow.com/questions/61272384/how-to-resize-matplotlib
        #  -figure-to-match-ipywidgets-output-size-automatically
        with self.out:
            self.fig, self.ax = plt.subplots(1, 1)  # , figsize=(5, 4), dpi=100)
            canvas = self.fig.canvas
            # canvas.toolbar_visible = False
            canvas.header_visible = False
            # canvas.footer_visible = False
            # canvas.resizable = False
            if hasattr(canvas, "layout"):
                canvas.layout.height = "100%"
                canvas.layout.width = "100%"
            plt.show()

    def _create_groove_dropdown(self):
        # get all attribute mappings (human-readable names)
        attrs = {
            attr
            for groove in _groove_name_to_type
            for attr in _groove_name_to_type[groove]._mapping.values()
        }

        # create dict with hboxes of all attributes
        self.groove_params_dropdowns = dict()
        param_widgets = self.groove_params_dropdowns
        for item in attrs:
            if item == "code_number":  # only the case for FFGroove
                dropdown = Dropdown(
                    options=get_ff_grove_code_numbers(),
                    layout=description_layout,
                )
                param_widgets[item] = HBox(
                    [Label(_("Code number"), layout=description_layout), dropdown]
                )
            else:
                # replace underscores with spaces, first letter uppercase, translate.
                t = f"{(item[0].upper() + item[1:]).replace('_', ' ')}"
                matches = re.match("(.*)([0-9]+)", t)
                if matches:
                    t = _(matches.group(1))
                    number = matches.group(2)
                    text = f"{t} {number}"
                else:
                    text = _(t)
                if "angle" in item:
                    param_widgets[item] = FloatWithUnit(text=text, unit="°", value=45)
                elif "workpiece_thickness" in item:
                    param_widgets[item] = FloatWithUnit(text=text, unit="mm", value=15)
                else:
                    param_widgets[item] = FloatWithUnit(text=text, unit="mm", value=5)
            param_widgets[item].mapping = item

        groove_list = list(_groove_name_to_type.keys())
        margin = 5
        groove_type_dropdown = Dropdown(
            options=groove_list,
            value=groove_list[1],  # VGroove
            layout=Layout(width=f"{2 * Q_(textbox_layout.width).m + margin}px"),
        )

        # connect value observers
        groove_type_dropdown.observe(self._update_params_to_selection, names="value")
        groove_type_dropdown.observe(self._update_plot, "value")
        self.add_parameter_observer(self._update_plot)

        return groove_type_dropdown

    def add_parameter_observer(self, observer: Callable):
        """Add observers to groove parameters."""
        for key, box in self.groove_params_dropdowns.items():
            box.children[1].observe(observer, "value")
            # if key != "code_number":
            #    box.children[2].observe(observer, "value")

    def _update_plot(self, *args):
        groove_type = self.groove_type_dropdown.value
        groove_obj = self._groove_obj_cache.get(groove_type, None)

        groove_params = dict(groove_type=groove_type)
        for child in self.groove_params.children:
            param_key = child.mapping
            if param_key == _("code_number"):
                groove_params[param_key] = child.children[1].value
            else:
                magnitude = child.children[1].value
                unit = child.children[2].value
                groove_params[param_key] = Q_(magnitude, unit)

        if groove_obj is None:
            self._groove_obj = get_groove(**groove_params)
            self._groove_obj_cache[groove_type] = groove_obj
        else:
            for attr, value in groove_params.items():
                setattr(groove_obj, attr, value)
            self.groove_obj = groove_obj

        # TODO: re-plot can be avoided (e.g. set_xydata?)
        self.ax.lines.clear()
        # self.ax.texts = []

        self.groove_obj.plot(line_style="-", ax=self.ax)
        self.ax.autoscale(True, axis="both")

    def _update_params_to_selection(self, change):
        selection = change["new"]
        self.groove_params.children = [
            slider
            for key, slider in self.groove_params_dropdowns.items()
            if key
            in (
                _groove_name_to_type[selection]._mapping[x]
                for x in _groove_name_to_type[selection]._mapping
            )
        ]


class WidgetGrooveSelectionTCPMovement(WidgetMyVBox):
    """Widget to combine groove type and tcp movement."""

    def __init__(self):
        self.last_plot: Optional[CoordinateSystemManagerVisualizerK3D] = None
        self.groove_sel = WidgetGrooveSelection()

        self.seam_length = FloatWithUnit(_("Seam length"), value=300, min=0, unit="mm")
        self.seam_length.observe_float_value(self.create_csm_and_plot)
        self.seam_length.observe_unit(self.create_csm_and_plot)

        self.tcp_y = FloatWithUnit("TCP-y", unit="mm")
        self.tcp_z = FloatWithUnit("TCP-z", unit="mm")
        # TODO: compute weld speed accordingly to chosen groove area!
        # TODO: consider setting it read-only??
        self.weld_speed = FloatWithUnit(_("weld speed"), value=6, unit="mm/s")
        self.base_metal = WidgetMetal()
        self.geometry_export = WidgetCADExport()
        self.additional_params = (
            make_title(_("Welding parameters"), 4),
            self.seam_length,
            self.weld_speed,
            self.tcp_y,
            self.tcp_z,
            self.base_metal,
        )
        # add our parameters to our instance of WidgetGrooveSelection.
        self.groove_sel.groove_selection.children += self.additional_params

        # add 3d plot and CAD export to groove_sel output tab
        self.out = Output()
        self.groove_sel.output_tabs.children += (self.out, self.geometry_export)
        self.groove_sel.output_tabs.set_title(1, "3D " + _("profile"))
        self.groove_sel.output_tabs.set_title(2, "CAD export")

        self.groove_sel.output_tabs.observe(
            self.create_csm_and_plot, names="selected_index"
        )
        self.groove_sel.add_parameter_observer(self.create_csm_and_plot)

        # csm 3d visualization
        self.csm = None

        children = [
            self.groove_sel,
        ]

        super(WidgetGrooveSelectionTCPMovement, self).__init__(
            children=children, layout=Layout(width="100%")
        )

    def create_csm_and_plot(self, change=None, plot=True, **kwargs):
        """Create coordinates system manager containing TCP movement."""
        if change is not None:
            # update, except for 2d view.
            if change.get("new", -1) == 0:
                return

        # TODO: only create once and then update the csm!

        # create a linear trace segment a the complete weld seam trace
        trace_segment = weldx.LinearHorizontalTraceSegment(self.seam_length.quantity)
        trace = weldx.Trace(trace_segment)

        # create 3d workpiece geometry from the groove profile and trace objects
        geometry = weldx.Geometry(
            self.groove_sel.groove_obj.to_profile(width_default=Q_(5, "mm")), trace
        )

        # rasterize geometry
        profile_raster_width = self.geometry_export.profile_raster_width.quantity
        trace_raster_width = self.geometry_export.trace_raster_width.quantity

        # crete a new coordinate system manager with default base coordinate system
        csm = weldx.CoordinateSystemManager(
            "base", coordinate_system_manager_name="design"
        )

        # add the workpiece coordinate system
        csm.add_cs(
            coordinate_system_name="workpiece",
            reference_system_name="base",
            lcs=trace.coordinate_system,
        )

        # add the geometry data of the specimen
        sp_specimen = geometry.spatial_data(profile_raster_width, trace_raster_width)
        sp_specimen.plot(backend="k3d")
        csm.assign_data(
            sp_specimen,
            "specimen",
            "workpiece",
        )
        self.geometry_export.geometry = sp_specimen

        tcp_y = self.tcp_y.float_value
        tcp_z = self.tcp_z.float_value
        tcp_start_point = Q_([5.0, tcp_y, tcp_z], "mm")
        tcp_end_point = Q_([self.seam_length.float_value - 5.0, tcp_y, tcp_z], "mm")

        v_weld = self.weld_speed.quantity
        s_weld = (tcp_end_point - tcp_start_point)[0]  # length of the weld
        t_weld = s_weld / v_weld

        t_start = pd.Timedelta("0s")
        t_end = pd.Timedelta(str(t_weld))

        rot = weldx.WXRotation.from_euler("x", 180, degrees=True)

        coords = np.stack([tcp_start_point, tcp_end_point])

        tcp_wire = weldx.LocalCoordinateSystem(
            coordinates=coords, orientation=rot, time=[t_start, t_end]
        )

        csm.add_cs(
            coordinate_system_name="TCP design",
            reference_system_name="workpiece",
            lcs=tcp_wire,
        )

        self.csm = csm

        if plot:
            self.plot()

    def plot(self):
        """Visualize the tcp design movement."""
        # clear previous output.
        if self.last_plot is not None:
            self.last_plot.close()

        with self.out:
            self.out.clear_output()
            vis = self.csm.plot(
                coordinate_systems=["TCP design"],
                # limits=[(0, 140), (-5, 5), (0, 12)],
                show_vectors=False,
                show_wireframe=False,
                backend="k3d",
            )
            display(vis)
        self.last_plot = vis.plot

    def to_tree(self) -> dict:
        """Return the workpiece, coordinates and TCP movement."""
        geometry = dict(
            **self.groove_sel.to_tree(),
            seam_length=self.seam_length.quantity,
        )
        workpiece = dict(geometry=geometry, **self.base_metal.to_tree())

        if self.csm is None:
            self.create_csm_and_plot(button=None, plot=False)
        # the single_pass_weld_schema expects the "TCP" key to be a LCS
        # TODO: has it any consequence later on, that we drop the reference to the CSM?
        tree = dict(
            workpiece=workpiece,
            # according to single_pass_weld schema of weldx we will add "coordinates"
            # later on.
            coordinates_design=self.csm,
            TCP=self.csm.get_cs("TCP design", "workpiece"),
        )
        return tree

    def from_tree(self, tree: dict):
        """Set widget groups state from given tree."""
        self.csm = tree.get("coordinates_design", None)
        workpiece = tree["workpiece"]
        geom = workpiece["geometry"]

        self.seam_length.quantity = geom["seam_length"]
        self.groove_sel.from_tree(geom)
        self.base_metal.from_tree(workpiece)
