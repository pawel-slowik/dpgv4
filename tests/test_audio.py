# pylint: disable=missing-docstring
from dpgv4 import check_for_audio_stream
from .util import sample_filename


def test_audio_stream_exists() -> None:
    input_filename = sample_filename("Test Image - 2141.mp4")
    assert check_for_audio_stream(input_filename) is False


def test_audio_stream_does_not_exist() -> None:
    input_filename = sample_filename("World - 2.mp4")
    assert check_for_audio_stream(input_filename) is True
