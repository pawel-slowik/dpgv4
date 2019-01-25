import unittest
from dpgv4 import calculate_dimensions
from .util import sample_filename

class TestDimensions(unittest.TestCase):

    def test_dimensions(self) -> None:
        input_filename = sample_filename("World - 2.mp4")
        self.assertEqual(calculate_dimensions(input_filename), (256, 144))
