"""Type aliases shared in visualization package."""

from typing import Union

import pandas as pd

types_timeindex = Union[pd.DatetimeIndex, pd.TimedeltaIndex, list[pd.Timestamp]]
types_limits = Union[list[tuple[float, float]], tuple[float, float]]

__all__ = ("types_timeindex", "types_limits")
