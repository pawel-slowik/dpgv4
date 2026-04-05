# pylint: disable=missing-docstring
from typing import Iterable, Mapping
import pytest
from dpgv4 import list_audio_streams, map_audio_id
from .util import sample_filename

# pylint: disable=redefined-outer-name; (for pytest fixtures)


def test_audio_stream_does_not_exist() -> None:
    input_filename = sample_filename("Test Image - 2141.mp4")
    assert len(tuple(list_audio_streams(input_filename))) == 0


def test_audio_stream_exists() -> None:
    input_filename = sample_filename("World - 2.mp4")
    assert len(tuple(list_audio_streams(input_filename))) > 0


def test_audio_stream_properties() -> None:
    input_filename = sample_filename("World - 2.mp4")
    streams = tuple(list_audio_streams(input_filename))
    assert "index" in streams[0]
    assert streams[0]["codec_type"] == "audio"


def test_audio_mapping_none(audio_streams: Iterable[Mapping]) -> None:
    assert map_audio_id(None, audio_streams) == 0


def test_audio_mapping_int(audio_streams: Iterable[Mapping]) -> None:
    assert map_audio_id(1, audio_streams) == 1


def test_audio_mapping_numeric_string(audio_streams: Iterable[Mapping]) -> None:
    assert map_audio_id("1", audio_streams) == 1


def test_audio_mapping_existing_language(audio_streams: Iterable[Mapping]) -> None:
    assert map_audio_id("eng", audio_streams) == 0
    assert map_audio_id("jpn", audio_streams) == 1


def test_audio_mapping_nonexistent_language(audio_streams: Iterable[Mapping]) -> None:
    assert map_audio_id("foo bar", audio_streams) == 0


@pytest.fixture
def audio_streams() -> Iterable[Mapping]:
    return [
        {
            "index": 2,
            "tags": {
                "language": "jpn",
            }
        },
        {
            "index": 1,
            "tags": {
                "language": "eng",
            }
        },
    ]
