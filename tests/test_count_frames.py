# pylint: disable=missing-docstring
from dpgv4 import count_video_frames
from .util import sample_filename

def test_count_frames() -> None:
    input_filename = sample_filename("Test Image - 2141.mp4")
    with open(input_filename, "rb") as input_file:
        frame_count = count_video_frames(input_file)
        assert frame_count == 900
