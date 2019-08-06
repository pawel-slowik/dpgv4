# pylint: disable=missing-docstring
from dpgv4 import create_screenshot, create_thumbnail
from .util import sample_filename

def test_screenshot() -> None:
    input_file = sample_filename("Test Image - 2141.mp4")
    expected_output_file = sample_filename("Test Image - 2141.screenshot")
    with open(input_file, "rb") as inp, open(expected_output_file, "rb") as expected:
        assert create_screenshot(inp, 10) == expected.read()

def test_thumbnail() -> None:
    # this is not a good test, because a change in PIL image scaling algorithm may cause
    # pixel differences and then the test will spuriously fail
    input_file = sample_filename("Test Image - 2141.screenshot")
    expected_output_file = sample_filename("Test Image - 2141.thumbnail")
    with open(input_file, "rb") as inp, open(expected_output_file, "rb") as expected:
        assert create_thumbnail(inp.read()) == expected.read()
