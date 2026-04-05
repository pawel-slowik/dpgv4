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
    )
)
def test_stream_matches_language(stream: Mapping, language: str, expected_match: bool) -> None:
    assert stream_matches_language(stream, language) == expected_match
