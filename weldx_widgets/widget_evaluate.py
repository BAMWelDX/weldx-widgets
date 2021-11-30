"""Contain widgets to evaluate a WeldxFile.

That includes:
0. ASDF header
1. Planned workpiece
2. Planned TCP
3. Measurements (and chains)
4. 3D-plots of design, measured (scan),
5. Parameters for the power source.

"""
from collections import defaultdict

import matplotlib.pyplot as plt
from IPython.core.display import display
from ipywidgets import Layout, Output, Tab

import weldx
from weldx import (
    Q_,
    Geometry,
    GmawProcess,
    LinearHorizontalTraceSegment,
    SpatialData,
    Trace,
    WeldxFile,
)
from weldx_widgets.widget_base import WidgetSimpleOutput
from weldx_widgets.widget_factory import make_title
from weldx_widgets.widget_measurement import WidgetMeasurement, WidgetMeasurementChain


class WidgetProcessInfo(WidgetSimpleOutput):
    """Plot GMAW process parameter into output widget."""

    def __init__(self, gmaw_process: GmawProcess, t, out=None):
        super(WidgetProcessInfo, self).__init__(out=out)

        children = [make_title("Process parameters"), self.out]
        self.children = children

        with self:
            from weldx_widgets.widget_gmaw import plot_gmaw

            self.fig, self.ax = plot_gmaw(gmaw_process, t)
            plt.show()


# Define some colors for the coordinate systems
cs_colors = {
    "workpiece": (100, 100, 100),
    "workpiece geometry": (100, 100, 100),
    "scan_0": (100, 100, 100),
    "scan_1": (100, 100, 100),
    "workpiece geometry (reduced)": (0, 0, 0),
    "user_frame": (180, 180, 0),
    "TCP": (255, 0, 0),
    "TCP design": (200, 0, 0),
    "T1": (0, 255, 0),
    "T2": (0, 200, 0),
    "T3": (0, 150, 0),
    "T4": (0, 100, 0),
    "welding_wire": (150, 150, 0),
    "flange": (0, 0, 255),
    "LLT_1": (40, 240, 180),
    "LLT_2": (20, 190, 150),
    "XIRIS_1": (255, 0, 255),
    "XIRIS_2": (200, 0, 200),
}


class WidgetEvaluateSinglePassWeld(Tab):
    """Aggregate info of passed file in several tabs."""

    def __init__(self, file_content: WeldxFile):
        def make_output():
            layout = Layout(width="100%", height="800px")
            out = Output(layout=layout)
            return out

        tabs = defaultdict(make_output)

        with tabs["ASDF-header"]:
            display(file_content.show_asdf_header(False, True))

        # start and end time of experiment
        t = (file_content["TCP"].time[[0, -1]]).as_timedelta()

        WidgetProcessInfo(
            file_content["process"]["welding_process"], t, out=tabs["Process params"]
        )

        groove = file_content["workpiece"]["geometry"]["groove_shape"]
        with tabs["Specimen"]:
            print("Material")
            print(file_content["workpiece"]["base_metal"]["common_name"])
            print(file_content["workpiece"]["base_metal"]["standard"])

            groove.plot()
            plt.show()

            seam_length = file_content["workpiece"]["geometry"]["seam_length"]
            print("Seam length:", seam_length)

        # 3D Geometry
        geometry = self._create_geometry(groove, seam_length, Q_(10, "mm"))
        # #with tabs["Workpiece"]:
        #     display(geometry.plot(profile_raster_width=Q_(4, "mm"),
        #                           trace_raster_width=Q_(40, "mm")))

        # Add geometry data to CSM
        csm = file_content["coordinate_systems"]

        geometry_full_width = self._create_geometry(groove, seam_length, Q_(100, "mm"))
        spatial_data_geo_full = geometry_full_width.spatial_data(
            profile_raster_width=Q_(4, "mm"), trace_raster_width=Q_(60, "mm")
        )
        spatial_data_geo_full.coordinates = spatial_data_geo_full.coordinates.astype(
            "float32"
        )

        spatial_data_geo_reduced = geometry.spatial_data(
            profile_raster_width=Q_(4, "mm"), trace_raster_width=Q_(60, "mm")
        )

        csm.assign_data(spatial_data_geo_full, "workpiece geometry", "workpiece")
        csm.assign_data(
            spatial_data_geo_reduced, "workpiece geometry (reduced)", "workpiece"
        )

        with tabs["CSM-Subsystems"]:
            csm.plot_graph()
            plt.show()
            self._show_csm_subsystems(csm)

        with tabs["CSM-Design"]:
            display(
                csm.plot(
                    reference_system="workpiece",
                    coordinate_systems=["TCP design", "T1", "T2"],
                    data_sets=["workpiece geometry (reduced)"],
                    colors=cs_colors,
                    show_wireframe=True,
                    show_data_labels=False,
                    show_vectors=False,
                    backend="k3d",
                )
            )

        welding_wire_diameter = file_content["process"]["welding_wire"]["diameter"].m
        csm.assign_data(
            self._welding_wire_geo_data(welding_wire_diameter / 2, 20, 16),
            "welding_wire",
            "TCP",
        )

        with tabs["CSM-Real"]:
            plt_real = csm.plot(
                reference_system="workpiece",
                coordinate_systems=["TCP", "T1", "T2"],
                data_sets=["scan_0", "welding_wire"],
                colors=cs_colors,
                show_data_labels=False,
                backend="k3d",
            )
            # plt_real.plot.width="100%"
            display(plt_real)

        # tcp = csm.get_cs("TCP design")
        # with self:
        #    print(tcp)

        measurements = file_content["measurements"]
        # TODO: compute W on the fly and attach it to measurements?
        WidgetMeasurementChain(measurements, out=tabs["Measurement chain"])
        WidgetMeasurement(measurements, out=tabs["Measurements"])

        with tabs["Plots"]:
            tabs["Plots"].clear_output()
            self._compare_design_tcp(csm)
            plt.show()

        super(WidgetEvaluateSinglePassWeld, self).__init__(
            children=tuple(tabs.values())
        )
        for i, key in enumerate(tabs.keys()):
            self.set_title(i, key)
        self.tabs = tabs

    @staticmethod
    def _show_csm_subsystems(csm):
        # Show subsystems
        print(csm.subsystem_names)
        subsystems = csm.subsystems
        fig, ax = plt.subplots(ncols=len(subsystems))
        for i, subsystem in enumerate(subsystems):
            subsystem.plot_graph(ax=ax[i])
        # _, ax = new_3d_figure_and_axes(num_subplots=2, width=700, height=700)
        vec_scaling = [[7, 12, 50], [36, 18, 1.2]]
        plt.show()
        for i, subsystem in enumerate(subsystems):
            display(
                subsystem.plot(
                    axes=ax[i],
                    colors=cs_colors,
                    show_vectors=True,
                    scale_vectors=vec_scaling[i],
                    backend="k3d",
                )
            )

    @staticmethod
    def _compare_design_tcp(csm):
        # TCP design vs TCP
        csm_interp = csm.interp_time(csm.time_union())
        tcp_design_coords = csm_interp.get_cs("TCP design", "workpiece").coordinates
        tcp_coords = csm_interp.get_cs("TCP", "workpiece").coordinates

        tcp_diff = tcp_design_coords - tcp_coords
        time = csm_interp.time_union()
        time = weldx.Time(time - time[0]).as_quantity()

        # difference in welding speed
        fig, ax = plt.subplots(1, 2)
        ax[0].plot(time.m, tcp_diff.data[:, 0])
        ax[0].set_title("Difference in welding speed")
        ax[0].set_xlabel("time in s")
        ax[0].set_ylabel("diff in mm")

        # diffs depend on how well the user frame matches
        ax[1].set_title("User frame deviation")
        ax[1].plot(time.m, tcp_diff.data[:, 1], label="y")
        ax[1].plot(time.m, tcp_diff.data[:, 2], label="z")
        ax[1].legend()

        ax[1].set_xlabel("time in s")
        ax[1].set_ylabel("diff in mm")

    @staticmethod
    def _welding_wire_geo_data(radius, length, cross_section_resolution=8):
        import numpy as np

        points = []
        triangles = []
        for i in range(cross_section_resolution):
            angle = i / cross_section_resolution * np.pi * 2
            x = np.cos(angle) * radius
            y = np.sin(angle) * radius
            points.append([x, y, 0])
            points.append([x, y, length])

            idx = 2 * i
            triangles.append([idx, idx + 1, idx + 3])
            triangles.append([idx, idx + 3, idx + 2])

        triangles[-2][2] = 1
        triangles[-1][1] = 1
        triangles[-1][2] = 0

        return SpatialData(
            np.array(points, dtype="float32"), np.array(triangles, dtype="uint32")
        )

    @staticmethod
    def _create_geometry(groove, seam_length, width):
        trace = Trace(LinearHorizontalTraceSegment(seam_length))
        return Geometry(groove.to_profile(width_default=width), trace)
