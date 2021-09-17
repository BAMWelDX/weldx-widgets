"""Wraps around a sophisticated video player."""
from jpy_video import Video

from weldx_widgets.widget_base import WidgetSimpleOutput


# TODO: eventually we do not need this.
class WidgetVideo(WidgetSimpleOutput):
    """Creates a video widget."""

    def __init__(self, video_path):
        super(WidgetVideo, self).__init__()

        with self.out:
            video_widget = Video(str(video_path))
            video_widget.layout.width = "640px"
        self.video = video_widget

        # p = video_widget.properties
        # p["playbackRate"] = 0.1  # TODO: does not work
