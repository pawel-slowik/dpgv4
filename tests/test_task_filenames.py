# pylint: disable=missing-docstring
import pytest
from dpgv4 import create_task_list

# one-to-one, a special case

def test_one_input_one_output() -> None:
    test = create_task_list({"input.mp4"}, "output.dpg")
    expected = [("input.mp4", "output.dpg")]
    assert test == expected

# `output is None` tests

def test_relative_input_no_output() -> None:
    test = create_task_list({"title.mkv"}, None)
    expected = [("title.mkv", "title.dpg")]
    assert test == expected

def test_absolute_input_no_output() -> None:
    test = create_task_list({"/tmp/title.mkv"}, None)
    expected = [("/tmp/title.mkv", "/tmp/title.dpg")]
    assert test == expected

def test_mixed_inputs_no_output() -> None:
    test = create_task_list({"title1.mp4", "/tmp/title2.mkv"}, None)
    expected = [
        ("title1.mp4", "title1.dpg"),
        ("/tmp/title2.mkv", "/tmp/title2.dpg"),
    ]
    assert sorted(test) == sorted(expected)

# `output is not None, input is relative` tests

def test_relative_input_relative_output() -> None:
    test = create_task_list({"title.mkv"}, "tmp")
    expected = [("title.mkv", "tmp/title.dpg")]
    assert test == expected

def test_relative_input_absolute_output() -> None:
    test = create_task_list({"title.mkv"}, "/tmp")
    expected = [("title.mkv", "/tmp/title.dpg")]
    assert test == expected

def test_multiple_relative_inputs_relative_output() -> None:
    test = create_task_list(
        {
            "title1.mkv",
            "foo/title2.mp4",
            "bar/title3.mp4",
        },
        "tmp"
    )
    expected = [
        ("title1.mkv", "tmp/title1.dpg"),
        ("foo/title2.mp4", "tmp/foo/title2.dpg"),
        ("bar/title3.mp4", "tmp/bar/title3.dpg"),
    ]
    assert sorted(test) == sorted(expected)

def test_multiple_relative_inputs_absolute_output() -> None:
    test = create_task_list(
        {
            "title1.mkv",
            "foo/title2.mp4",
            "bar/title3.mp4",
        },
        "/tmp"
    )
    expected = [
        ("title1.mkv", "/tmp/title1.dpg"),
        ("foo/title2.mp4", "/tmp/foo/title2.dpg"),
        ("bar/title3.mp4", "/tmp/bar/title3.dpg"),
    ]
    assert sorted(test) == sorted(expected)

# `output is not None, input is absolute` tests

def test_absolute_input_relative_output() -> None:
    test = create_task_list({"/tmp/title.mkv"}, "foo")
    expected = [("/tmp/title.mkv", "foo/title.dpg")]
    assert test == expected

def test_absolute_input_absolute_output() -> None:
    test = create_task_list({"/tmp/title.mkv"}, "/foo")
    expected = [("/tmp/title.mkv", "/foo/title.dpg")]
    assert test == expected

def test_multiple_absolute_inputs_relative_output() -> None:
    test = create_task_list(
        {
            "/tmp/title1.mkv",
            "/tmp/foo/title2.mp4",
            "/tmp/bar/title3.mp4",
        },
        "baz"
    )
    expected = [
        ("/tmp/title1.mkv", "baz/title1.dpg"),
        ("/tmp/foo/title2.mp4", "baz/foo/title2.dpg"),
        ("/tmp/bar/title3.mp4", "baz/bar/title3.dpg"),
    ]
    assert sorted(test) == sorted(expected)

def test_multiple_absolute_inputs_absolute_output() -> None:
    test = create_task_list(
        {
            "/tmp/title1.mkv",
            "/tmp/foo/title2.mp4",
            "/tmp/bar/title3.mp4",
        },
        "/baz"
    )
    expected = [
        ("/tmp/title1.mkv", "/baz/title1.dpg"),
        ("/tmp/foo/title2.mp4", "/baz/foo/title2.dpg"),
        ("/tmp/bar/title3.mp4", "/baz/bar/title3.dpg"),
    ]
    assert sorted(test) == sorted(expected)

# `output is not None, input is mixed` tests

def test_mixed_inputs_relative_output() -> None:
    with pytest.raises(ValueError):
        create_task_list({"title1.mkv", "/tmp/title2.mp4"}, "tmp")

def test_mixed_inputs_absolute_output() -> None:
    with pytest.raises(ValueError):
        create_task_list({"title1.mkv", "/tmp/title2.mp4"}, "/tmp")
