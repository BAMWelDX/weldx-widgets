"""Widgets to select groove type and tcp movement."""
from __future__ import annotations

import ipywidgets as widgets
import matplotlib.pyplot as plt
import pandas as pd
from IPython.display import clear_output
from ipywidgets import Button, HBox, Label, Layout, Output, VBox

import weldx
from weldx.constants import WELDX_QUANTITY as Q_
from weldx.welding.groove.iso_9692_1 import _groove_name_to_type, get_groove
from weldx_widgets.generic import show_only_exception_message
from weldx_widgets.widget_base import (
    WeldxImportExport,
    WidgetMyHBox,
    WidgetMyVBox,
    WidgetSimpleOutput,
)
from weldx_widgets.widget_factory import (
    FloatWithUnit,
    WidgetLabeledTextInput,
    button_layout,
    description_layout,
    hbox_float_text_creator,
    layout_generic_output,
    make_title,
    plot_layout,
)

__all__ = [
    "WidgetGrooveSelection",
    "WidgetGrooveSelectionTCPMovement",
]


class WidgetMetal(WidgetMyVBox):
    """Widget to select metal type and parameters."""

    def __init__(self):
        self.common_name = WidgetLabeledTextInput("Common name", "S355J2+N")
        self.standard = WidgetLabeledTextInput("Standard", "DIN EN 10225-2:2011")
        self.thickness = FloatWithUnit("Thickness", value=30, unit="mm")
        children = [
            make_title("Base metal"),
            self.common_name,
            self.standard,
            self.thickness,
        ]
        super(WidgetMetal, self).__init__(children=children)

    def to_tree(self):
        """Return metal parameters."""
        return dict(
            common_name=self.common_name.text_value,
            standard=self.standard.text_value,
            thickness=self.thickness.quantity,
        )


def get_code_numbers():
    """Return FFGroove code numbers."""
    from weldx.welding.groove.iso_9692_1 import FFGroove

    try:
        a = FFGroove.__annotations__
        return a["code_number"].__args__
    except AttributeError:
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

    # TODO: filename/WeldxFile as input arg?
    def __init__(self):
        self.out = Output(layout=layout_generic_output)
        self.out.layout = plot_layout
        self.groove_obj = None  # current groove object
        self.hbox_dict = None  # TODO: better name

        # create figure for groove visualization
        self._create_plot()

        self.groove_params_vbox = WidgetMyVBox([])
        self.groove_type_dropdown = self._create_groove_dropdown()
        # self.save_button = self._create_save_button()
        # create rest
        self.groove_selection = WidgetMyVBox(
            [
                self.groove_type_dropdown,
                self.groove_params_vbox,
                WidgetMyVBox([]),  # additional parameters (e.g. weld speed).
            ]
        )
        children = [
            make_title("ISO 9692-1 Groove selection", 3),
            WidgetMyHBox(children=[self.groove_selection, self.out]),
        ]

        # set initial state
        self._update_params_to_selection(dict(new=self.groove_type_dropdown.value))
        self._update_plot(None)
        super(WidgetGrooveSelection, self).__init__(
            children=children, layout=Layout(width="100%")
        )

    @property
    def schema(self) -> str:
        """Return schema."""
        raise NotImplementedError

    def from_tree(self, tree: dict):
        """Fill widget from tree."""
        self.groove_obj = tree["groove"]
        raise NotImplementedError
        # TODO: update fields according to data in new groove obj!

    def to_tree(self) -> dict:
        """Return groove parameters."""
        return dict(groove=self.groove_obj)

    # TODO: replace with SAveButton widget
    def _create_save_button(self):
        self.button_o = widgets.Output()
        self.filename = widgets.Text("groove.weldx", layout=description_layout)

        def on_button_clicked(_):
            # TODO: set output filename and save it!
            with self.button_o:
                clear_output()
                tree = {"groove": self.groove_obj}
                print("vis tree....")
                with weldx.WeldxFile(tree=tree, mode="rw") as fh:
                    fh.show_asdf_header(True, True)

        # button
        b = Button(description="Show as .yml File", layout=button_layout)
        b.on_click(on_button_clicked)

        box = VBox([self.filename, b, self.button_o])
        return box

    def _create_plot(self):
        with self.out:
            self.fig, self.ax = plt.subplots(1, 1, figsize=(5, 4), dpi=100)
            canvas = self.fig.canvas
            canvas.toolbar_visible = False
            canvas.header_visible = False
            canvas.footer_visible = False
            canvas.resizable = False
            # plt.show(self.fig)

    def _create_groove_dropdown(self):
        # get all attribute mappings (human-readable names)
        attrs = {
            attr
            for groove in _groove_name_to_type
            for attr in _groove_name_to_type[groove]._mapping.values()
        }

        # TODO: formatting, first letter upper case, replace _ with space

        # create dict with hboxes of all attributes
        self.hbox_dict = dict()
        hbox_dict = self.hbox_dict
        for item in attrs:
            if item == "code_number":
                dropdown = widgets.Dropdown(
                    # import those somewhere?
                    options=get_code_numbers(),
                    layout=description_layout,
                )
                hbox_dict[item] = HBox(
                    [Label("code_number :", layout=description_layout), dropdown]
                )
            elif "angle" in item:
                hbox_dict[item] = hbox_float_text_creator(item, "deg", 45)
            elif "workpiece_thickness" in item:
                hbox_dict[item] = hbox_float_text_creator(item, "mm", 15)
            else:
                hbox_dict[item] = hbox_float_text_creator(item, "mm", 5)

        groove_list = list(_groove_name_to_type.keys())
        # TODO: layout
        groove_type_dropdown = widgets.Dropdown(
            options=groove_list,
            value=groove_list[1],
            description="Groove type",
        )

        # connect value observers
        groove_type_dropdown.observe(self._update_params_to_selection, names="value")

        update_plot = self._update_plot
        groove_type_dropdown.observe(update_plot, "value")
        for key, box in hbox_dict.items():
            box.children[1].observe(update_plot, "value")
            if key != "code_number":
                box.children[2].observe(update_plot, "value")

        return groove_type_dropdown

    def _update_plot(self, _):
        selection = self.groove_type_dropdown.value
        with self.out:
            groove_params = dict()
            groove_params["groove_type"] = selection
            for child in self.groove_params_vbox.children:
                child_0 = child.children[0]
                if child_0.value == "code_number":
                    groove_params[child_0.value] = child.children[1].value
                else:
                    magnitude = child.children[1].value
                    unit = child.children[2].value
                    groove_params[child_0.value] = Q_(magnitude, unit)

            self.groove_obj = get_groove(**groove_params)
            # TODO: replot can be avoided (e.g. set_xydata?)
            self.ax.lines = []
            # self.ax.texts = []

            with show_only_exception_message():
                self.groove_obj.plot(line_style="-", ax=self.ax)

    def _update_params_to_selection(self, change):
        selection = change["new"]
        self.groove_params_vbox.children = [
            slider
            for key, slider in self.hbox_dict.items()
            if key
            in (
                _groove_name_to_type[selection]._mapping[x]
                for x in _groove_name_to_type[selection]._mapping
            )
        ]


class WidgetGrooveSelectionTCPMovement(WidgetMyVBox):
    """Widget to combine groove type and tcp movement."""

    def __init__(self):
        self.groove_sel = WidgetGrooveSelection()
        self.seam_length = FloatWithUnit("Seam length", value=300, min=0, unit="mm")
        self.tcp_y = FloatWithUnit("TCP-y", unit="mm")
        self.tcp_z = FloatWithUnit("TCP-z", unit="mm")
        # TODO: compute weld speed accordingly to chosen groove area!
        # TODO: consider setting it read-only??
        self.weld_speed = FloatWithUnit("weld speed", value=6, unit="mm/s")
        self.base_metal = WidgetMetal()
        self.additional_params = (
            make_title("Welding parameters", 4),
            self.seam_length,
            self.weld_speed,
            self.tcp_y,
            self.tcp_z,
            self.base_metal,
        )
        # add our parameters to our instance of WidgetGrooveSelection.
        self.groove_sel.groove_selection.children += self.additional_params
        self.csm = None
        self.out = WidgetSimpleOutput(height="800px", width="auto")
        self.out.set_visible(False)
        self.plot_button = Button(description="3D Plot", layout=button_layout)
        self.plot_button.on_click(self.create_csm_and_plot)

        children = [
            self.groove_sel,
            self.plot_button,
            self.out,
        ]

        super(WidgetGrooveSelectionTCPMovement, self).__init__(
            children=children, layout=Layout(width="100%")
        )

    def create_csm_and_plot(self, button, plot=True, **kwargs):
        """Create coordinates system manager containing TCP movement."""
        # TODO: only create once and then update the csm!

        # create a linear trace segment a the complete weld seam trace
        trace_segment = weldx.LinearHorizontalTraceSegment(self.seam_length.quantity)
        trace = weldx.Trace(trace_segment)

        # create 3d workpiece geometry from the groove profile and trace objects
        geometry = weldx.Geometry(
            self.groove_sel.groove_obj.to_profile(width_default=Q_(5, "mm")), trace
        )

        # rasterize geometry
        profile_raster_width = Q_(2, "mm")  # resolution of each profile in mm
        trace_raster_width = Q_(30, "mm")  # space between profiles in mm

        # TODO: show 2d data?
        # geometry_data_sp = geometry.rasterize(
        #     profile_raster_width=profile_raster_width,
        #     trace_raster_width=trace_raster_width
        # )

        # crete a new coordinate system manager with default base coordinate system
        csm = weldx.CoordinateSystemManager("base")

        # add the workpiece coordinate system
        csm.add_cs(
            coordinate_system_name="workpiece",
            reference_system_name="base",
            lcs=trace.coordinate_system,
        )

        # add the geometry data of the specimen
        csm.assign_data(
            geometry.spatial_data(profile_raster_width, trace_raster_width),
            "specimen",
            "workpiece",
        )

        tcp_y = self.tcp_y.float_value
        tcp_z = self.tcp_z.float_value
        # tcp_start_point = Q_([5.0, 0.0, 2.0], "mm")
        # tcp_end_point = Q_([self.seam_length.float_value - 5.0, 0.0, 2.0], "mm")
        tcp_start_point = Q_([5.0, tcp_y, tcp_z], "mm")
        tcp_end_point = Q_([self.seam_length.float_value - 5.0, tcp_y, tcp_z], "mm")

        v_weld = self.weld_speed.quantity
        s_weld = (tcp_end_point - tcp_start_point)[0]  # length of the weld
        t_weld = s_weld / v_weld

        t_start = pd.Timedelta("0s")
        t_end = pd.Timedelta(str(t_weld))

        rot = weldx.WXRotation.from_euler("x", 180, degrees=True)

        coords = [tcp_start_point.magnitude, tcp_end_point.magnitude]

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
        self.out.set_visible(True)
        self.out.out.clear_output()
        # TODO: close older figures to regain resources!
        # TODO: can old figures be updated?
        with self.out:
            self.csm.plot(
                coordinate_systems=["TCP design"],
                # colors=color_dict,
                # limits=[(0, 140), (-5, 5), (0, 12)],
                show_vectors=False,
                show_wireframe=False,
                backend="k3d",
            )

    def to_tree(self) -> dict:
        """Return the workpiece, coordinates and TCP movement."""
        geometry = dict(
            groove_shape=self.groove_sel.groove_obj,
            seam_length=self.seam_length.quantity,
        )
        base_metal = dict(common_name="S355J2+N", standard="DIN EN 10225-2:2011")
        workpiece = dict(base_metal=base_metal, geometry=geometry)
        if self.csm is None:
            self.create_csm_and_plot(button=None, plot=False)
        # the single_pass_weld_schema expects the "TCP" key to be a LCS
        # TODO: has it any consequence later on, that we drop the reference to the CSM?
        tree = dict(
            workpiece=workpiece,
            coordinates=self.csm,
            TCP=self.csm.get_cs("TCP design", "workpiece"),
        )
        return tree
