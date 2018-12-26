import unittest
from dpgv4 import create_screenshot, create_thumbnail
from .util import sample_filename

class TestThumbnail(unittest.TestCase):

    def test_screenshot(self):
        input_file = sample_filename("Test Image - 2141.mp4")
        expected_output_file = sample_filename("Test Image - 2141.screenshot")
        with open(input_file, "rb") as inp, open(expected_output_file, "rb") as expected:
            self.assertEqual(create_screenshot(inp, 10), expected.read())

    def test_thumbnail(self):
        # this is not a good test, because a change in PIL image scaling algorithm may cause
        # pixel differences and then the test will spuriously fail
        input_file = sample_filename("Test Image - 2141.screenshot")
        expected_output_file = sample_filename("Test Image - 2141.thumbnail")
        with open(input_file, "rb") as inp, open(expected_output_file, "rb") as expected:
            self.assertEqual(create_thumbnail(inp.read()), expected.read())
