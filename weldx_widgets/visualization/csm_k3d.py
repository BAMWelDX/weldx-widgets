"""Contains some functions to help with visualization."""

from __future__ import annotations

from typing import TYPE_CHECKING, Union

import k3d
import k3d.colormaps.matplotlib_color_maps
import k3d.platonic as platonic
import numpy as np
import pandas as pd
import pint
from ipywidgets import Checkbox, Dropdown, HBox, IntSlider, Layout, Play, VBox, jslink

import weldx.geometry as geo
from weldx.constants import _DEFAULT_LEN_UNIT as _DL
from weldx.core import TimeSeries

if TYPE_CHECKING:  # pragma: no cover
    from weldx.transformations.local_cs import LocalCoordinateSystem

from .colors import (
    RGB_BLACK,
    RGB_BLUE,
    RGB_GREEN,
    RGB_GREY,
    RGB_RED,
    color_generator_function,
    get_color,
)
from .types import types_limits, types_timeindex

__all__ = [
    "CoordinateSystemManagerVisualizerK3D",
    "SpatialDataVisualizer",
]


def _get_limits_from_stack(limits):
    mins = limits.min(axis=0)[0, :]
    maxs = limits.max(axis=0)[1, :]
    return np.vstack([mins, maxs])


def _get_coordinates_and_orientation(
    lcs: LocalCoordinateSystem, index: int = 0
) -> tuple[pint.Quantity, pint.Quantity]:
    """Get the coordinates and orientation of a coordinate system.

    Parameters
    ----------
    lcs :
        The coordinate system
    index :
        If the coordinate system is time dependent, the passed value is the index
        of the values that should be returned

    Returns
    -------
    coordinates
        The coordinates
    orientation
        The orientation
    """
    if isinstance(lcs.coordinates, TimeSeries):
        raise ValueError(
            "Can not visualize LCS with expression based coordinates. "
            "Interpolate values before plotting to solve this issue"
        )

    coordinates = lcs.coordinates.isel(time=index, missing_dims="ignore").data.astype(
        "float32"
    )

    orientation = lcs.orientation.isel(time=index, missing_dims="ignore").data.astype(
        "float32"
    )

    return coordinates, orientation


def _create_model_matrix(
    coordinates: pint.Quantity, orientation: np.ndarray
) -> np.ndarray:
    """Create the model matrix from an orientation and coordinates.

    Parameters
    ----------
    coordinates :
        The coordinates of the origin
    orientation :
        The orientation of the coordinate system

    Returns
    -------
    np.ndarray:
        The model matrix
    """
    model_matrix = np.eye(4, dtype="float32")
    model_matrix[:3, :3] = orientation
    model_matrix[:3, 3] = coordinates.to(_DL).m
    return model_matrix


class CoordinateSystemVisualizerK3D:
    """Visualizes a `weldx.transformations.LocalCoordinateSystem` using k3d."""

    def __init__(
        self,
        lcs: LocalCoordinateSystem,
        plot: k3d.Plot = None,
        name: str = None,
        color: int = RGB_BLACK,
        show_origin=True,
        show_trace=True,
        show_vectors=True,
        vector_scale=2.5,
    ):
        """Create a `CoordinateSystemVisualizerK3D`.

        Parameters
        ----------
        lcs :
            Coordinate system that should be visualized
        plot :
            A k3d plotting widget.
        name :
            Name of the coordinate system
        color :
            The RGB color of the coordinate system (affects trace and label) as a 24 bit
            integer value.
        show_origin :
            If `True`, the origin of the coordinate system will be highlighted in the
            color passed as another parameter
        show_trace :
            If `True`, the trace of a time dependent coordinate system will be
            visualized in the color passed as another parameter
        show_vectors :
            If `True`, the the coordinate axes of the coordinate system are visualized
        """
        coordinates, orientation = _get_coordinates_and_orientation(lcs)
        self._lcs = lcs
        self._color = color
        self._vector_scale = vector_scale

        self._vectors = k3d.vectors(
            origins=[coordinates.to(_DL).m for _ in range(3)],
            vectors=orientation.transpose() * self._vector_scale,
            line_width=0.05,
            head_size=3.0,
            colors=[[RGB_RED, RGB_RED], [RGB_GREEN, RGB_GREEN], [RGB_BLUE, RGB_BLUE]],
            labels=[],
            label_size=1.5,
            name=name if name is None else f"{name} (vectors)",
        )
        self._vectors.visible = show_vectors

        self._label = None
        if name is not None:
            self._label = k3d.text(
                text=name,
                position=coordinates.to(_DL).m + 0.05,
                color=self._color,
                size=1,
                label_box=False,
                name=name if name is None else f"{name} (text)",
                is_html=True,
            )

        self._trace = k3d.line(
            np.array(lcs.coordinates.data.to(_DL).m, dtype="float32"),  # type: ignore
            shader="thick",
            width=0.1,  # change with .set_trait("width", value)
            color=color,
            name=name if name is None else f"{name} (line)",
        )
        self._trace.visible = show_trace

        self.origin = platonic.Octahedron(size=0.1).mesh
        self.origin.color = color
        self.origin.model_matrix = _create_model_matrix(coordinates, orientation)
        self.origin.visible = show_origin

        if plot is not None:
            plot += self._vectors
            plot += self._trace
            plot += self.origin
            if self._label is not None:
                plot += self._label

    def _update_positions(self, coordinates: pint.Quantity, orientation: np.ndarray):
        """Update the positions of the coordinate cross and label.

        Parameters
        ----------
        coordinates :
            The new coordinates
        orientation :
            The new orientation
        """
        self._vectors.origins = [coordinates for _ in range(3)]
        self._vectors.vectors = orientation.transpose() * self._vector_scale
        self.origin.model_matrix = _create_model_matrix(coordinates, orientation)
        if self._label is not None:
            self._label.position = coordinates.to(_DL).m + 0.05

    def show_label(self, show_label: bool):
        """Set the visibility of the label.

        Parameters
        ----------
        show_label :
            If `True`, the label will be shown
        """
        self._label.visible = show_label

    def show_origin(self, show_origin: bool):
        """Set the visibility of the coordinate systems' origin.

        Parameters
        ----------
        show_origin :
            If `True`, the coordinate systems origin is shown.
        """
        self.origin.visible = show_origin

    def show_trace(self, show_trace: bool):
        """Set the visibility of coordinate systems' trace.

        Parameters
        ----------
        show_trace :
            If `True`, the coordinate systems' trace is shown.
        """
        self._trace.visible = show_trace

    def show_vectors(self, show_vectors: bool):
        """Set the visibility of the coordinate axis vectors.

        Parameters
        ----------
        show_vectors :
            If `True`, the coordinate axis vectors are shown.
        """
        self._vectors.visible = show_vectors

    def update_lcs(self, lcs: LocalCoordinateSystem, index: int = 0):
        """Pass a new coordinate system to the visualizer.

        Parameters
        ----------
        lcs :
            The new coordinate system
        index :
            The time index of the new coordinate system that should be visualized.
        """
        self._lcs = lcs
        self._trace.vertices = np.array(
            lcs.coordinates.data.to(_DL).m,  # type: ignore[union-attr]
            dtype="float32",
        )
        self.update_time_index(index)

    def update_time_index(self, index: int):
        """Update the plotted time step.

        Parameters
        ----------
        index : int
            The array index of the time step
        """
        coordinates, orientation = _get_coordinates_and_orientation(self._lcs, index)
        self._update_positions(coordinates, orientation)

    def limits(self):
        lcs = self._lcs
        dims = [d for d in lcs.coordinates.dims if d != "c"]
        if dims:
            mins = lcs.coordinates.min(dim=dims).data
            maxs = lcs.coordinates.max(dim=dims).data
            return np.vstack([mins, maxs])
        return np.vstack([lcs.coordinates.data, lcs.coordinates.data])


class SpatialDataVisualizer:
    """Visualizes spatial data."""

    visualization_methods = ["auto", "point", "mesh", "both"]

    def __init__(
        self,
        data: Union[np.ndarray, geo.SpatialData],
        name: str,
        reference_system: str,
        plot: k3d.Plot = None,
        color: int = None,
        visualization_method: str = "auto",
        show_wireframe: bool = False,
        create_points: bool = False,
        create_label: bool = False,
    ):
        """Create a ``SpatialDataVisualizer`` instance.

        Parameters
        ----------
        data :
            The data that should be visualized
        name :
            Name of the data
        reference_system :
            Name of the data's reference system
        plot :
            A k3d plotting widget.
        color :
            The RGB color of the coordinate system (affects trace and label) as a 24 bit
            integer value.
        visualization_method :
            The initial data visualization method. Options are ``point``, ``mesh``,
            ``both``and ``auto``. If ``auto`` is selected, a mesh will be drawn if
            triangle data is available and points if not.
        show_wireframe :
            If `True`, meshes will be drawn as wireframes
        create_points
            create points object even if mesh is available
        create_label
            create a K3D label for the data
        """
        if not isinstance(data, geo.SpatialData):
            data = geo.SpatialData(coordinates=data)

        colors = []  # color mapping for 3d data
        if color is None or isinstance(color, str):
            if isinstance(color, str):
                colors = data.attributes[color]
            color = RGB_GREY

        self._color = color

        if data.triangles is not None:
            triangles = data.triangles.astype(np.uint32)
        else:
            triangles = None

        self._reference_system = reference_system

        self.data = data

        self._label = None
        if create_label & (name is not None):
            self.create_label(name=name)

        self._points = None
        if (data.triangles is None) | create_points:
            self._points = k3d.points(
                self.data.coordinates.data.to(_DL).m,
                point_size=0.05,
                color=self._color,
                name=name if name is None else f"{name} (points)",
            )

        self._mesh = None
        _coords = self.data.coordinates.data
        if isinstance(_coords, pint.Quantity):
            _coords = _coords.to(_DL).m

        if data.triangles is not None:
            self._mesh = k3d.mesh(
                _coords.astype(np.float32).reshape(-1, 3),
                triangles,
                side="double",
                color=self._color,
                attribute=colors,
                color_map=k3d.colormaps.matplotlib_color_maps.Viridis,
                wireframe=show_wireframe,
                name=name if name is None else f"{name} (mesh)",
            )

        self.set_visualization_method(visualization_method)

        if plot is not None:
            self.add_to_plot(plot)

    def create_label(self, name):
        """Create a K3D label for this object."""
        dims = self.data.additional_dims
        self._label_pos = self.data.coordinates.mean(dim=dims).data.to(_DL).m
        if name is not None:
            self._label = k3d.text(
                text=name,
                position=self._label_pos,
                reference_point="cc",
                color=self._color,
                size=0.5,
                label_box=True,
                name=name if name is None else f"{name} (text)",
                is_html=True,
            )

    def add_to_plot(self, plot: k3d.Plot):
        """Add the k3d objects t an existing plot."""
        if self._points is not None:
            plot += self._points
        if self._mesh is not None:
            plot += self._mesh
        if self._label is not None:
            plot += self._label

    @property
    def reference_system(self) -> str:
        """Get the name of the reference coordinate system.

        Returns
        -------
        str :
            Name of the reference coordinate system
        """
        return self._reference_system

    def set_visualization_method(self, method: str):
        """Set the visualization method.

        Parameters
        ----------
        method : str
            The data visualization method. Options are ``point``, ``mesh``, ``both`` and
            ``auto``. If ``auto`` is selected, a mesh will be drawn if triangle data is
            available and points if not.
        """
        if method not in SpatialDataVisualizer.visualization_methods:
            raise ValueError(f"Unknown visualization method: '{method}'")

        if method == "auto":
            if self._mesh is not None:
                method = "mesh"
            else:
                method = "point"

        if self._points is not None:
            self._points.visible = method in ["point", "both"]

        if self._mesh is not None:
            self._mesh.visible = method in ["mesh", "both"]

    def show_label(self, show_label: bool):
        """Set the visibility of the label.

        Parameters
        ----------
        show_label : bool
            If `True`, the label will be shown
        """
        if self._label is not None:
            self._label.visible = show_label

    def show_wireframe(self, show_wireframe: bool):
        """Set wireframe rendering.

        Parameters
        ----------
        show_wireframe : bool
            If `True`, the mesh will be rendered as wireframe
        """
        if self._mesh is not None:
            self._mesh.wireframe = show_wireframe

    def update_model_matrix(self, model_mat):
        """Update the model matrices of the k3d objects."""
        if self._points is not None:
            self._points.model_matrix = model_mat
        if self._mesh is not None:
            self._mesh.model_matrix = model_mat
        if self._label is not None:
            self._label.position = (
                np.matmul(model_mat[0:3, 0:3], self._label_pos) + model_mat[0:3, 3]
            )


class CoordinateSystemManagerVisualizerK3D:
    """Visualizes a `weldx.transformations.CoordinateSystemManager` using k3d."""

    def __init__(
        self,
        csm,
        coordinate_systems: list[str] = None,
        data_sets: list[str] = None,
        colors: dict[str, Union[int, tuple[int, int, int]]] = None,
        reference_system: str = None,
        title: str = None,
        limits: types_limits = None,
        time: types_timeindex = None,
        time_ref: pd.Timestamp = None,
        show_data_labels: bool = True,
        show_labels: bool = True,
        show_origins: bool = True,
        show_traces: bool = True,
        show_vectors: bool = True,
        show_wireframe: bool = True,
        plot_all_obj: bool = False,
    ):
        """Create a `CoordinateSystemManagerVisualizerK3D`.

        Parameters
        ----------
        csm : weldx.transformations.CoordinateSystemManager
            The `weldx.transformations.CoordinateSystemManager` instance that should be
            visualized
        coordinate_systems :
            The names of the coordinate systems that should be visualized. If ´None´ is
            provided, all systems are plotted
        data_sets :
            The names of data sets that should be visualized. If ´None´ is provided, all
            data is plotted
        colors :
            A mapping between a coordinate system name or a data set name and a color.
            The colors must be provided as 24 bit integer values that are divided into
            three 8 bit sections for the rgb values. For example ``0xFF0000`` for pure
            red.
            Each coordinate system or data set that does not have a mapping in this
            dictionary will get a default color assigned to it.
        reference_system :
            Name of the initial reference system. If `None` is provided, the root system
            of the `weldx.transformations.CoordinateSystemManager` instance will be used
        title :
            The title of the plot
        limits :
            The limits of the plotted volume
        time :
            The time steps that should be plotted initially
        time_ref :
            A reference timestamp that can be provided if the ``time`` parameter is a
            `pandas.TimedeltaIndex`
        show_data_labels :
            If `True`, the data labels will be shown initially
        show_labels  :
            If `True`, the coordinate system labels will be shown initially
        show_origins :
            If `True`, the coordinate systems' origins will be shown initially
        show_traces :
            If `True`, the coordinate systems' traces will be shown initially
        show_vectors :
            If `True`, the coordinate systems' axis vectors will be shown initially
        show_wireframe :
            If `True`, spatial data containing mesh data will be drawn as wireframe
        """
        if time is None:
            time = csm.time_union()
        if time is not None:
            csm = csm.interp_time(time=time, time_ref=time_ref)

        self._csm = csm.interp_time(time=time, time_ref=time_ref)
        self._current_time_index = 0

        if coordinate_systems is None:
            coordinate_systems = csm.coordinate_system_names
        if data_sets is None:
            data_sets = self._csm.data_names
        if reference_system is None:
            reference_system = self._csm.root_system_name
        self._current_reference_system = reference_system

        plot = k3d.plot()
        self.plot = plot

        self._color_generator = color_generator_function()

        self._lcs_vis = {
            lcs_name: CoordinateSystemVisualizerK3D(
                self._csm.get_cs(lcs_name, reference_system),
                plot,
                lcs_name,
                color=get_color(lcs_name, colors, self._color_generator),
                show_origin=show_origins,
                show_trace=show_traces,
                show_vectors=show_vectors,
            )
            for lcs_name in coordinate_systems
        }
        self._data_vis = {
            data_name: SpatialDataVisualizer(
                self._csm.get_data(data_name=data_name),
                data_name,
                self._csm.get_data_system_name(data_name=data_name),
                plot,
                color=get_color(data_name, colors, self._color_generator),
                show_wireframe=show_wireframe,
                create_label=plot_all_obj,
                create_points=plot_all_obj,
            )
            for data_name in data_sets
        }
        self._update_spatial_data()

        # create controls
        self._controls = self._create_controls(
            time,
            show_data_labels,
            show_labels,
            show_origins,
            show_traces,
            show_vectors,
            show_wireframe,
        )

        # add title
        self._title = None
        if title is not None:
            self._title = k3d.text2d(
                f"<b>{title}</b>",
                position=(0.5, 0),
                color=RGB_BLACK,
                is_html=True,
                size=1.5,
                reference_point="ct",
            )
            plot += self._title

        # add time info
        self._time = time
        self._time_ref = time_ref
        self._time_info = None
        if time is not None:
            self._time_info = k3d.text2d(
                f"<b>time:</b> {time[0]}",
                position=(0, 1),
                color=RGB_BLACK,
                is_html=True,
                size=1.0,
                reference_point="lb",
                name="timeline",
            )
            plot += self._time_info

        # workaround since using it inside the init method of the coordinate system
        # visualizer somehow causes the labels to be created twice with one version
        # being always visible
        self.show_data_labels(show_data_labels)
        self.show_labels(show_labels)

        self._plot = plot
        if limits is None:
            limits = self._get_limits()
        self.grid = limits

    @property
    def grid(self):
        """Return the plot grid bounding box in (x0, y0, z0, x1, y1, z1) format."""
        return self._plot.grid

    @grid.setter
    def grid(self, value):
        """Set grid bounding box in (x0, y0, z0, x1, y1, z1) or (min, max) format."""
        if value is None:
            self._plot.grid_auto_fit = True
            self._plot.grid = (-1, -1, -1, 1, 1, 1)
        else:
            self._plot.grid_auto_fit = False
            if isinstance(value, pint.Quantity):
                value = value.to(_DL).m
            grid = tuple(np.array(value).flatten().astype(int))
            if len(grid) == 2:
                grid = np.repeat(grid, 3)
            self._plot.grid = grid

    def _get_limits_spatial(self):
        """Get the limits of all spatial data."""
        if not self._data_vis:
            return None
        limits = np.stack([s.data.limits() for s in self._data_vis.values()])
        return _get_limits_from_stack(limits)

    def _get_limits_trace(self):
        """Get the limits of all LCS/traces."""
        if not self._lcs_vis:
            return None
        limits = np.stack([lcs_vis.limits() for lcs_vis in self._lcs_vis.values()])
        return _get_limits_from_stack(limits)

    def _get_limits(self):
        limits_spatial = self._get_limits_spatial()
        limits_trace = self._get_limits_trace()
        limits = [lims for lims in [limits_spatial, limits_trace] if lims is not None]
        if limits:
            return _get_limits_from_stack(np.stack(limits))
        return None

    def _ipython_display_(self):
        from IPython.core.display import display

        # display everything
        self._plot.display()
        display(self._controls)

    def _create_controls(
        self,
        time: types_timeindex,
        show_data_labels: bool,
        show_labels: bool,
        show_origins: bool,
        show_traces: bool,
        show_vectors: bool,
        show_wireframe: bool,
    ):
        """Create the control panel.

        Parameters
        ----------
        time : pandas.DatetimeIndex, pandas.TimedeltaIndex, list[pandas.Timestamp], or \
               LocalCoordinateSystem
            The time steps that should be plotted initially
        show_data_labels : bool
            If `True`, the data labels will be shown initially
        show_labels  : bool
            If `True`, the coordinate system labels will be shown initially
        show_origins : bool
            If `True`, the coordinate systems' origins will be shown initially
        show_traces : bool
            If `True`, the coordinate systems' traces will be shown initially
        show_vectors : bool
            If `True`, the coordinate systems' axis vectors will be shown initially
        show_wireframe : bool
            If `True`, spatial data containing mesh data will be drawn as wireframe
        """
        num_times = 1
        disable_time_widgets = True
        lo = Layout(width="200px")

        # create widgets
        if time is not None:
            num_times = len(time)
            disable_time_widgets = False

        play = Play(
            min=0,
            max=num_times - 1,
            value=self._current_time_index,
            step=1,
        )
        time_slider = IntSlider(
            min=0,
            max=num_times - 1,
            value=self._current_time_index,
            description="Time:",
        )
        reference_dropdown = Dropdown(
            options=self._csm.coordinate_system_names,
            value=self._current_reference_system,
            description="Reference:",
            disabled=False,
        )
        data_dropdown = Dropdown(
            options=SpatialDataVisualizer.visualization_methods,
            value="auto",
            description="data repr.:",
            disabled=False,
            layout=lo,
        )

        lo = Layout(width="200px")
        vectors_cb = Checkbox(value=show_vectors, description="show vectors", layout=lo)
        origin_cb = Checkbox(value=show_origins, description="show origins", layout=lo)
        traces_cb = Checkbox(value=show_traces, description="show traces", layout=lo)
        labels_cb = Checkbox(value=show_labels, description="show labels", layout=lo)
        wf_cb = Checkbox(value=show_wireframe, description="show wireframe", layout=lo)
        data_labels_cb = Checkbox(
            value=show_data_labels, description="show data labels", layout=lo
        )

        jslink((play, "value"), (time_slider, "value"))
        play.disabled = disable_time_widgets
        time_slider.disabled = disable_time_widgets

        # register callbacks
        time_slider.observe(lambda c: self.update_time_index(c["new"]), names="value")
        reference_dropdown.observe(
            lambda c: self.update_reference_system(c["new"]), names="value"
        )
        vectors_cb.observe(lambda c: self.show_vectors(c["new"]), names="value")
        origin_cb.observe(lambda c: self.show_origins(c["new"]), names="value")
        traces_cb.observe(lambda c: self.show_traces(c["new"]), names="value")
        labels_cb.observe(lambda c: self.show_labels(c["new"]), names="value")
        data_dropdown.observe(
            lambda c: self.set_data_visualization_method(c["new"]), names="value"
        )
        data_labels_cb.observe(lambda c: self.show_data_labels(c["new"]), names="value")
        wf_cb.observe(lambda c: self.show_wireframes(c["new"]), names="value")

        # create control panel
        row_1 = HBox([time_slider, play, reference_dropdown])
        row_2 = HBox([vectors_cb, origin_cb, traces_cb, labels_cb])
        if len(self._data_vis) > 0:
            row_3 = HBox([data_dropdown, wf_cb, data_labels_cb])
            return VBox([row_1, row_2, row_3])
        return VBox([row_1, row_2])

    def _get_model_matrix(self, lcs_name):
        lcs_vis = self._lcs_vis.get(lcs_name)
        if lcs_vis is not None:
            return lcs_vis.origin.model_matrix

        lcs = self._csm.get_cs(lcs_name, self._current_reference_system)
        coordinates, orientation = _get_coordinates_and_orientation(
            lcs, self._current_time_index
        )
        return _create_model_matrix(coordinates, orientation)

    def _update_spatial_data(self):
        for _, data_vis in self._data_vis.items():
            model_matrix = self._get_model_matrix(data_vis.reference_system)
            data_vis.update_model_matrix(model_matrix)

    def set_data_visualization_method(self, representation: str):
        """Set the data visualization method.

        Parameters
        ----------
        representation : str
            The data visualization method. Options are ``point``, ``mesh``, ``both`` and
            ``auto``. If ``auto`` is selected, a mesh will be drawn if triangle data is
            available and points if not.
        """
        for _, data_vis in self._data_vis.items():
            data_vis.set_visualization_method(representation)

    def show_data_labels(self, show_data_labels: bool):
        """Set the visibility of data labels.

        Parameters
        ----------
        show_data_labels: bool
            If `True`, labels are shown.
        """
        for _, data_vis in self._data_vis.items():
            data_vis.show_label(show_data_labels)

    def show_labels(self, show_labels: bool):
        """Set the visibility of the coordinate systems' labels.

        Parameters
        ----------
        show_labels : bool
            If `True`, the coordinate systems' labels are shown.
        """
        for _, lcs_vis in self._lcs_vis.items():
            lcs_vis.show_label(show_labels)

    def show_origins(self, show_origins: bool):
        """Set the visibility of the coordinate systems' origins.

        Parameters
        ----------
        show_origins : bool
            If `True`, the coordinate systems origins are shown.
        """
        for _, lcs_vis in self._lcs_vis.items():
            lcs_vis.show_origin(show_origins)

    def show_traces(self, show_traces: bool):
        """Set the visibility of coordinate systems' traces.

        Parameters
        ----------
        show_traces : bool
            If `True`, the coordinate systems' traces are shown.
        """
        for _, lcs_vis in self._lcs_vis.items():
            lcs_vis.show_trace(show_traces)

    def show_vectors(self, show_vectors: bool):
        """Set the visibility of the coordinate axis vectors.

        Parameters
        ----------
        show_vectors : bool
            If `True`, the coordinate axis vectors are shown.
        """
        for _, lcs_vis in self._lcs_vis.items():
            lcs_vis.show_vectors(show_vectors)

    def show_wireframes(self, show_wireframes: bool):
        """Set if meshes should be drawn in wireframe mode.

        Parameters
        ----------
        show_wireframes : bool
            If `True`, meshes are rendered as wireframes
        """
        for _, data_vis in self._data_vis.items():
            data_vis.show_wireframe(show_wireframes)

    def update_reference_system(self, reference_system):
        """Update the reference system of the plot.

        Parameters
        ----------
        reference_system : str
            Name of the new reference system
        """
        self._current_reference_system = reference_system
        for lcs_name, lcs_vis in self._lcs_vis.items():
            lcs_vis.update_lcs(
                self._csm.get_cs(lcs_name, reference_system), self._current_time_index
            )
        self._update_spatial_data()

    def update_time_index(self, index: int):
        """Update the plotted time by index.

        Parameters
        ----------
        index : int
            The new index
        """
        self._current_time_index = index
        for _, lcs_vis in self._lcs_vis.items():
            lcs_vis.update_time_index(index)
        self._update_spatial_data()
        self._time_info.text = f"<b>time:</b> {self._time[index]}"
