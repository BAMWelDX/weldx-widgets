"""Widget showing scanner results."""
from pathlib import Path
from typing import Tuple

import numpy as np
import xarray as xr
from tqdm.autonotebook import tqdm

import weldx
from weldx_widgets.widget_base import WidgetSimpleOutput

__all__ = ["WidgetScans"]


# TODO: handle both cases, parameterstudie (mehrere schweißungen auf einem werkstück)
# und einzel schweißung!
class WidgetScans(WidgetSimpleOutput):
    """Extracts triggers and scan data from given files and visualizes it.

    Parameters
    ----------
    mh24_file :
        path to twincat main file.
    tool_file :
        path to yaskawa tool file.
    scans_dir :
        path to scan directory.
    single_weld :
        Just one scan, or multiple?
    max_scans :
        limit for scans to read in/visualize.
    """

    def __init__(
        self, mh24_file, tool_file, scans_dir, single_weld=False, max_scans=None
    ):
        super(WidgetScans, self).__init__(width="100%", height="800 px")

        self.mh24_file = Path(mh24_file)
        self.tool_file = Path(tool_file)
        self.scans_dir = Path(scans_dir)
        assert self.scans_dir.exists()
        assert self.mh24_file.exists()
        assert self.tool_file.exists()

        self.max_scans = max_scans
        self.single_weld = single_weld

        from cached_io import read_cached_txt

        mh24_ds = read_cached_txt(mh24_file)
        from libo.utils import split_by_trigger

        mh_scan_list = split_by_trigger(mh24_ds, "trigScan1_prog")
        mh_schweiss_list = split_by_trigger(mh24_ds, "trigSchweissen")

        self.csm = weldx.CoordinateSystemManager("user_frame")

        self._create_csm(mh_schweiss_list)
        self._vorher_nachher_scans_an_csm(mh_scan_list)

    def _create_csm(self, mh_schweiss_list):
        for mh_schweiss in mh_schweiss_list[: self.max_scans]:
            coords = mh_schweiss[["UF_X", "UF_Y", "UF_Z"]].dropna(dim="time")
            coords = (
                coords.to_array(dim="c")
                .assign_coords(dict(c=["x", "y", "z"]))
                .astype("float32")
            )
            coords_start = coords.isel(time=0).drop("time")
            tcp_start = weldx.LocalCoordinateSystem(coordinates=coords_start)
            tpc_in_uf = weldx.LocalCoordinateSystem(coordinates=coords - coords_start)
            naht_NR = int(mh_schweiss.naht_NR.max().values)
            self.csm.add_cs(f"n_start{naht_NR}", "user_frame", tcp_start)
            self.csm.add_cs(f"n{naht_NR}", f"n_start{naht_NR}", tpc_in_uf)

    def _vorher_nachher_scans_an_csm(self, mh_scan_list):
        scans = []
        # TODO: handle self.single_weld (different pattern needed).
        if self.single_weld:
            _slice = slice(1, self.max_scans, 2)
            n = len(mh_scan_list[_slice])
            mh_scan_list_i = iter(mh_scan_list[_slice])
        else:
            _slice = slice(1, self.max_scans)
            mh_scan_list_i = iter(mh_scan_list[_slice])
            n = len(mh_scan_list[_slice])
        self._max_heights = []
        with self.out:
            for mh_scan in tqdm(mh_scan_list_i, total=n, desc="process scan data"):
                naht_nr = int(mh_scan.naht_NR.max().values)
                schw_nr = int(mh_scan.schw_NR.max().values)
                pattern = f"LLT1_WID*_N{naht_nr:03d}_L001_R001_S{schw_nr}_*.nc"
                scans_list = list(self.scans_dir.glob(pattern))
                assert len(scans_list) == 1

                SCAN_file = scans_list[0]
                scan = xr.load_dataset(SCAN_file)

                res = self._build_scan_data(mh_scan, scan)
                scan_name = f"scan_N{naht_nr}_S{schw_nr}"
                scans.append(scan_name)
                res = self.csm.transform_data(res, "user_frame", f"n_start{naht_nr}")
                # determine max value and store it for later display
                # TODO: max should return use only z-dimension
                max_height = res.coordinates.max(dim="n")
                print(max_height)
                self._max_heights.append(max_height[2])
                self.csm.assign_data(res, scan_name, f"n_start{naht_nr}")
                self.csm.assign_data(
                    max_height, scan_name + "max_h", f"n_start{naht_nr}"
                )
        self.scans = scans

    def display(self):
        """Render all pairs of scans and tcp movements."""
        scans = [
            f"n{x}"
            for x in range(1, self.max_scans - 1 if self.max_scans else len(self.scans))
        ]
        self.out.clear_output()
        with self.out:
            self.csm.plot(
                backend="k3d",
                coordinate_systems=["user_frame"] + scans,
                data_sets=self.scans,
                axes_equal=True,
            )
            # from matplotlib.pylab import plot

            # plot(self._max_heights)
            # TODO: add maximum height points and descriptions
            # import k3d

            # for i, max_ in enumerate(self._max_heights):
            #     max_heights = k3d.points(
            #         positions=max_.T, point_size=3, name="max height %i" % i
            #     )
            #     vis.plot += max_heights

    def _build_scan_data(
        self,
        mh_scan,
        scan: xr.Dataset,
    ) -> weldx.SpatialData:
        """Create transformed scan SpatialData from robot movement and LLT scan data.

        Parameters
        ----------
        mh_scan:
            The pre sliced trigger information
            create by e.g. ``split_by_trigger(mh24, "trigScan1_prog")``
        scan:
            The scan data as loaded xr.Dataset

        Returns
        -------
        weldx.SpatialData
            The scan data transformed into default user_frame
        """
        from libo.io.yaskawa import create_csm
        from libo.utils import get_data_transformation

        # load tool CSM --------------------------------------------------------------
        csm_tool = create_csm(self.tool_file)
        csm_tool.relabel({"STANDARD": "TCP"})
        csm_tool.add_cs(
            "LLT_1_data",
            "LLT_1",
            lcs=weldx.LocalCoordinateSystem(
                coordinates=[0, 0, -260],
                orientation=weldx.WXRotation.from_euler("z", -90, degrees=True),
            ),
        )

        lcs = get_data_transformation(mh_scan)

        # build and reshape scan data -------------------------------------------------
        data, triangle_indices = self._reshape_scan_data(scan, lcs)

        data[(data[:, 2] < -250), 2] = np.nan  # simple outliner removal
        data[(data[:, 2] > 50), 2] = np.nan  # simple outliner removal
        sd = weldx.SpatialData(
            coordinates=data.astype("float32"),
            triangles=triangle_indices.astype("uint32"),
        )

        return sd

    def _reshape_scan_data(
        self,
        ds: xr.Dataset,
        lcs: weldx.LocalCoordinateSystem,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Transform data gathered by LLT Dashboard into userframe coordinates.

        Parameters
        ----------
        ds:
            scan-dataset produced by LLT Dashboard
        lcs:
            LocalCoordinateSystem that describes the movement of
            the LLT Scanner during scan.

        Returns
        -------
            xyz-Data and default triangulation of profile-scan

        """
        nx = ds.n.shape[0]
        ny = ds.p.shape[0]

        ds["y"] = (("p", "n"), np.zeros((ny, nx)))

        data_arr = ds[["x", "y", "z"]].to_array("c")

        transformed = weldx.util.xr_matmul(
            lcs.orientation, data_arr, dims_a=["c", "v"], dims_b=["c"], dims_out=["c"]
        )
        # TODO: input param!
        n_slice = slice(450, 800)
        transformed = transformed + lcs.coordinates.rename({"time": "p"})
        transformed = transformed.isel(n=n_slice)

        ds = transformed.to_dataset(dim="c")

        nx = ds.n.shape[0]
        ny = ds.p.shape[0]

        data = np.zeros((nx * ny, 3))
        data[:, 0] = ds.x.data.flatten()
        data[:, 1] = ds.y.data.flatten()
        data[:, 2] = ds.z.data.flatten()

        triangle_indices = np.empty((ny - 1, nx - 1, 2, 3), dtype=int)
        r = np.arange(nx * ny).reshape(ny, nx)
        triangle_indices[:, :, 0, 0] = r[:-1, :-1]
        triangle_indices[:, :, 1, 0] = r[:-1, 1:]
        triangle_indices[:, :, 0, 1] = r[:-1, 1:]

        triangle_indices[:, :, 1, 1] = r[1:, 1:]
        triangle_indices[:, :, :, 2] = r[1:, :-1, None]
        triangle_indices.shape = (-1, 3)

        return data, triangle_indices


if __name__ == "__main__":
    from kisa_config import p_base

    WID = 432
    base = p_base / f"WID{WID}"

    TOOL_file = p_base / "MH24_TOOL.CND"
    MH24_file = list((base / "MAIN").glob("*_MH24_MAIN_AutoSave.txt.gz"))[0]

    WidgetScans(MH24_file, TOOL_file, base / "SCAN", max_scans=4).display()
