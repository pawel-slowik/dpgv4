# pylint: disable=missing-docstring
import pytest
from dpgv4 import create_header
from .util import sample_filename


def test_header_size() -> None:
    header = create_header(1, 1, 1, 1, 1)
    assert len(header) == 52


def test_known_good_header() -> None:
    header = create_header(722, 24, 488448, 643705, 488)
    expected = open(sample_filename("World - 2.header"), "rb").read()
    assert header == expected


def test_crash_on_frame_count_range() -> None:
    with pytest.raises(Exception):
        create_header(2**32, 1, 1, 1, 1)


def test_crash_on_framerate_range() -> None:
    with pytest.raises(Exception):
        create_header(1, 2**32, 1, 1, 1)


def test_crash_on_audio_size_range() -> None:
    with pytest.raises(Exception):
        create_header(1, 1, 2**32, 1, 1)


def test_crash_on_video_size_range() -> None:
    with pytest.raises(Exception):
        create_header(1, 1, 1, 2**32, 1)


def test_crash_on_gop_size_range() -> None:
    with pytest.raises(Exception):
        create_header(1, 1, 1, 1, 2**32)
