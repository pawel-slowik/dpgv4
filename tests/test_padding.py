# pylint: disable=missing-docstring
import pytest
from dpgv4 import VideoDimensions, calculate_padding


def test_no_padding() -> None:
    padding = calculate_padding(VideoDimensions(width=256, height=192))
    assert padding.horizontal == 0
    assert padding.vertical == 0


def test_horizontal_video_vertical_padding() -> None:
    padding = calculate_padding(VideoDimensions(width=256, height=100))
    assert padding.horizontal == 0
    assert padding.vertical == 46


def test_vertical_video_horizontal_padding() -> None:
    padding = calculate_padding(VideoDimensions(width=100, height=192))
    assert padding.horizontal == 78
    assert padding.vertical == 0


def test_exception_on_unscaled_width() -> None:
    with pytest.raises(ValueError):
        calculate_padding(VideoDimensions(width=300, height=192))


def test_exception_on_unscaled_height() -> None:
    with pytest.raises(ValueError):
        calculate_padding(VideoDimensions(width=256, height=200))
