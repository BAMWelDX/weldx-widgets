"""Test functions of the visualization package."""

import matplotlib.pyplot as plt
import pandas as pd
import pytest

import weldx.transformations as tf
import weldx_widgets.visualization as vs
from weldx.constants import Q_


def test_plot_coordinate_system():
    """Test executing all possible code paths."""
    lcs_constant = tf.LocalCoordinateSystem()

    time = pd.TimedeltaIndex([10, 11, 12], "s")
    orientation_tdp = [
        [[1, 0, 0], [0, 1, 0], [0, 0, 1]],
        [[0, 1, 0], [-1, 0, 0], [0, 0, 1]],
        [[-1, 0, 0], [0, -1, 0], [0, 0, 1]],
    ]
    coordinates_tdp = Q_([[0, 0, 1], [0, 0, 2], [0, -1, 0]], "mm")
    lcs_tdp = tf.LocalCoordinateSystem(orientation=orientation_tdp, coordinates=coordinates_tdp, time=time)

    _, ax = plt.subplots(subplot_kw=dict(projection="3d"))

    vs.draw_coordinate_system_matplotlib(lcs_constant, ax, "g")
    vs.draw_coordinate_system_matplotlib(lcs_tdp, ax, "r", "2016-01-10")
    vs.draw_coordinate_system_matplotlib(lcs_tdp, ax, "b", "2016-01-11", time_idx=1)
    vs.draw_coordinate_system_matplotlib(lcs_tdp, ax, "y", "2016-01-12", pd.TimedeltaIndex([12], "s"))

    # exceptions ------------------------------------------

    # label without color
    with pytest.raises(ValueError):
        vs.draw_coordinate_system_matplotlib(lcs_constant, ax, label="label")


def test_axes_equal():
    """Test executing all possible code paths."""
    _, ax = plt.subplots(subplot_kw=dict(projection="3d"))
    vs.axes_equal(ax)
