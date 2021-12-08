"""Test k3d implementations."""
import pytest

import weldx
from weldx import CoordinateSystemManager, Time, get_groove
from weldx_widgets.visualization.csm_k3d import CoordinateSystemManagerVisualizerK3D


@pytest.mark.parametrize("plot_all", (True, False))
def test_k3d_csm_vis(plot_all):
    """Create a simple CSM instance for k3d visualization."""
    csm = CoordinateSystemManager("base")
    csm.create_cs("A", "base", coordinates=[1, 1, 1])
    csm.create_cs(
        "B", "base", coordinates=[[0, 0, 0], [1, 2, 3]], time=Time(["0s", "1s"])
    )

    groove = get_groove(
        groove_type="VGroove",
        workpiece_thickness="1 cm",
        groove_angle="55 deg",
        root_gap="2 mm",
        root_face="1 mm",
    )

    spatial = weldx.Geometry(groove, "10mm").spatial_data("1 mm", "1 mm")
    csm.assign_data(spatial, "workpiece", "A")

    plot = CoordinateSystemManagerVisualizerK3D(csm=csm,plot_all_obj=plot_all)
    for state in [True, False, True]:
        plot.show_data_labels(state)
        plot.show_labels(state)
        plot.show_origins(state)
        plot.show_traces(state)
        plot.show_vectors(state)
        plot.show_wireframes(state)
    plot.update_reference_system("A")
