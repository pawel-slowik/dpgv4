# pylint: disable=missing-docstring
from dpgv4 import calculate_dimensions
from .util import sample_filename


def test_dimensions() -> None:
    input_filename = sample_filename("World - 2.mp4")
    dimensions = calculate_dimensions(input_filename)
    assert dimensions.width == 256
    assert dimensions.height == 144
