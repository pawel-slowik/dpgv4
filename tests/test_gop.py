import unittest
from dpgv4 import create_gop
from .util import sample_filename

class TestGOP(unittest.TestCase):

    def test_gop(self):
        input_file = sample_filename("Test Image - 2141.mp4")
        expected_output_file = sample_filename("Test Image - 2141.gop")
        with open(input_file, "rb") as inp, open(expected_output_file, "rb") as expected:
            gop = create_gop(inp)
            self.assertEqual(gop, expected.read())
