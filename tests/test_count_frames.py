import unittest
from dpgv4 import count_video_frames
from .util import sample_filename

class TestCountFrames(unittest.TestCase):

    def test_count_frames(self) -> None:
        input_filename = sample_filename("Test Image - 2141.mp4")
        with open(input_filename, "rb") as input_file:
            frame_count = count_video_frames(input_file)
            self.assertEqual(frame_count, 900)
