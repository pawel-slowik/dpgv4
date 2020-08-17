# pylint: disable=missing-docstring
from dpgv4 import list_subtitle_streams, parse_subtitle_stream_id, subtitle_options
from .util import sample_filename


def test_count_zero() -> None:
    input_filename = sample_filename("Test Image - 2141.mp4")
    assert len(tuple(list_subtitle_streams(input_filename))) == 0


def test_parse_none() -> None:
    input_filename = sample_filename("Test Image - 2141.mp4")
    assert parse_subtitle_stream_id(input_filename, None) is None


def test_parse_zero() -> None:
    input_filename = sample_filename("Test Image - 2141.mp4")
    assert parse_subtitle_stream_id(input_filename, 0) == 0


def test_parse_negative() -> None:
    input_filename = sample_filename("Test Image - 2141.mp4")
    assert parse_subtitle_stream_id(input_filename, -1) is None


def test_parse_external() -> None:
    assert parse_subtitle_stream_id(sample_filename("World - 2.mp4"), None) == 0


def test_parse_internal_by_language() -> None:
    input_filename = sample_filename("World - 2 (with subtitles).mkv")
    assert parse_subtitle_stream_id(input_filename, "eng") == 0


def test_parse_internal_by_title() -> None:
    input_filename = sample_filename("World - 2 (with subtitles).mkv")
    assert parse_subtitle_stream_id(input_filename, "English") == 0


def test_options_no_external_none() -> None:
    input_filename = sample_filename("Test Image - 2141.mp4")
    assert subtitle_options(input_filename, None, None) == []


def test_options_no_external_zero() -> None:
    input_filename = sample_filename("Test Image - 2141.mp4")
    input_index = 0
    expected_filename = input_filename
    expected_index = 0
    options = list(subtitle_options(input_filename, input_index, None))
    assert len(options) >= 2
    assert expected_filename in options[1]
    assert "stream_index=%d" % expected_index in options[1]


def test_options_no_external_one() -> None:
    input_filename = sample_filename("Test Image - 2141.mp4")
    input_index = 1
    expected_filename = input_filename
    expected_index = 1
    options = list(subtitle_options(input_filename, input_index, None))
    assert len(options) >= 2
    assert expected_filename in options[1]
    assert "stream_index=%d" % expected_index in options[1]


def test_options_external_none() -> None:
    input_filename = sample_filename("World - 2.mp4")
    assert subtitle_options(input_filename, None, None) == []


def test_options_external_zero() -> None:
    input_filename = sample_filename("World - 2.mp4")
    input_index = 0
    expected_filename = sample_filename("World - 2.srt")
    expected_index = 0
    options = list(subtitle_options(input_filename, input_index, None))
    assert len(options) >= 2
    assert expected_filename in options[1]
    assert "stream_index=%d" % expected_index in options[1]


def test_options_external_one() -> None:
    input_filename = sample_filename("World - 2.mp4")
    input_index = 1
    expected_filename = input_filename
    expected_index = 0
    options = list(subtitle_options(input_filename, input_index, None))
    assert len(options) >= 2
    assert expected_filename in options[1]
    assert "stream_index=%d" % expected_index in options[1]
