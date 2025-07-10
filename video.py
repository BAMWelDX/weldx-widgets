from pathlib import Path

import pandas as pd


def create_axis_video(
    start_end_time: tuple[str | pd.Timestamp],
    output: str | Path,
    *,
    speedup: float = None,
    default_tz="Europe/Berlin",
    video_root_path: str | Path = "/mnt/axis_recordings/",
    camera_serial: str = "ACCC8ED0F345",
    out_of_range: str = "warning",
):
    """Create a cut video file from a longer axis recording based on start and end time.

    The created video will start at the provided start time and end at the end time.
    Timezone information in provided timestamps is supported.
    The camera has to be selected by providing the camera serial number `camera_serial`.

    Parameters
    ----------
    start_end_time
        A tuple containing the desired start and end time as timestamp.
        Times can be given as `pandas.Timestamp` or `string`.
        Times that are given as string are trying to be converted to `pandas.Timestamp`

        Timestamps can (and should) be given with timezone information.
        If no timezone information is provided, the timestamp is interpreted
        based on the `default_tz`
        parameter (see below).
    output:
        The output filename or directory.
    speedup, optional
        A factor to speedup the video.
        Example: providing a speedup of 3 will reduce the final video length to 1/3 of
        the original length.
        No speedup if parameter is not provided.
    default_tz, optional
        The default timezone to interpret all timestamps without
        timezone information (naive), by default "Europe/Berlin"
    video_root_path, optional
        The root path from where to start looking for videos,
        by default "/mnt/axis_recordings/"
    camera_serial, optional
        The camera serial number to look for in the root path, by default "ACCC8ED0F345"
    out_of_range, optional
        Determine if the user is displayed a "warning" or "error" when the provided
        timestamps are out of the range of the original video, by default "warning"

    """
    pass
