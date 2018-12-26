import unittest
from dpgv4 import get_aspect_ratio
from .util import sample_filename

class TestAspectRatio(unittest.TestCase):

    def test_aspect_ratio(self):
        input_filename = sample_filename("Test Image - 2141.mp4")
        self.assertEqual(get_aspect_ratio(input_filename), 4 / 3)
