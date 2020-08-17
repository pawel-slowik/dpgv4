# pylint: disable=missing-docstring
from dpgv4 import calculate_dimensions
from .util import sample_filename


def test_dimensions() -> None:
    input_filename = sample_filename("World - 2.mp4")
    assert calculate_dimensions(input_filename) == (256, 144)
