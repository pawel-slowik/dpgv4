# pylint: disable=missing-docstring
from typing import Mapping
import pytest
from dpgv4 import stream_matches_language


@pytest.mark.parametrize(
    "stream,language,expected_match",
    (
        pytest.param(
            {"language": "eng", "title": "English"},
            "eng",
            False,
            id="missing tags",
        ),
        pytest.param(
            {"tags": {"language": "eng", "title": "English"}},
            "en1",
            False,
            id="none of the tags matches",
        ),

        pytest.param(
            {"tags": {"language": "eng"}},
            "eng",
            True,
            id="exact match on language tag",
        ),
        pytest.param(
            {"tags": {"language": "eng"}},
            "ENG",
            True,
            id="case insensitive match on language tag",
        ),
        pytest.param(
            {"tags": {"language": "English[eng]"}},
            "eng",
            True,
            id="word match on language tag",
        ),
        pytest.param(
            {"tags": {"language": "English[eng]"}},
            "english",
            True,
            id="case insensitive word match on language tag",
        ),

        pytest.param(
            {"tags": {"LANGUAGE": "eng"}},
            "eng",
            True,
            id="exact match on LANGUAGE tag",
        ),
        pytest.param(
            {"tags": {"LANGUAGE": "eng"}},
            "ENG",
            True,
            id="case insensitive match on LANGUAGE tag",
        ),
        pytest.param(
            {"tags": {"LANGUAGE": "English[eng]"}},
            "eng",
            True,
            id="word match on LANGUAGE tag",
        ),
        pytest.param(
            {"tags": {"LANGUAGE": "English[eng]"}},
            "ENG",
            True,
            id="case insensitive word match on LANGUAGE tag",
        ),

        pytest.param(
            {"tags": {"title": "English"}},
            "English",
            True,
            id="exact match on title tag",
        ),
        pytest.param(
            {"tags": {"title": "English"}},
            "ENGLISH",
            True,
            id="case insensitive match on title tag",
        ),
        pytest.param(
            {"tags": {"title": "English[eng]"}},
            "eng",
            True,
            id="word match on title tag",
        ),
        pytest.param(
            {"tags": {"title": "English[eng]"}},
            "ENGLISH",
            True,
            id="case insensitive word match on title tag",
        ),

        pytest.param(
            {"tags": {"title": "English 2.0 stereo"}},
            "2",
            False,
            id="no match on irrelevant part",
        ),
    )
)
def test_stream_matches_language(stream: Mapping, language: str, expected_match: bool) -> None:
    assert stream_matches_language(stream, language) == expected_match
