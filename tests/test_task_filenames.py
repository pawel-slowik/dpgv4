# pylint: disable=missing-docstring
import pytest
from dpgv4 import create_task_list


# one-to-one, a special case


def test_one_input_one_output() -> None:
    test = list(create_task_list({"input.mp4"}, "output.dpg"))
    assert len(test) == 1
    assert test[0].input_file == "input.mp4"
    assert test[0].output_file == "output.dpg"


# `output is None` tests


def test_relative_input_no_output() -> None:
    test = list(create_task_list({"title.mkv"}, None))
    assert len(test) == 1
    assert test[0].input_file == "title.mkv"
    assert test[0].output_file == "title.dpg"


def test_absolute_input_no_output() -> None:
    test = list(create_task_list({"/tmp/title.mkv"}, None))
    assert len(test) == 1
    assert test[0].input_file == "/tmp/title.mkv"
    assert test[0].output_file == "/tmp/title.dpg"


def test_mixed_inputs_no_output() -> None:
    test = list(sorted((create_task_list({"title1.mp4", "/tmp/title2.mkv"}, None))))
    assert len(test) == 2
    assert test[0].input_file == "/tmp/title2.mkv"
    assert test[0].output_file == "/tmp/title2.dpg"
    assert test[1].input_file == "title1.mp4"
    assert test[1].output_file == "title1.dpg"


# `output is not None, input is relative` tests


def test_relative_input_relative_output() -> None:
    test = list(create_task_list({"title.mkv"}, "tmp"))
    assert len(test) == 1
    assert test[0].input_file == "title.mkv"
    assert test[0].output_file == "tmp/title.dpg"


def test_relative_input_absolute_output() -> None:
    test = list(create_task_list({"title.mkv"}, "/tmp"))
    assert len(test) == 1
    assert test[0].input_file == "title.mkv"
    assert test[0].output_file == "/tmp/title.dpg"


def test_multiple_relative_inputs_relative_output() -> None:
    test = list(sorted(create_task_list(
        {
            "title1.mkv",
            "foo/title2.mp4",
            "bar/title3.mp4",
        },
        "tmp"
    )))
    assert len(test) == 3
    assert test[0].input_file == "bar/title3.mp4"
    assert test[0].output_file == "tmp/bar/title3.dpg"
    assert test[1].input_file == "foo/title2.mp4"
    assert test[1].output_file == "tmp/foo/title2.dpg"
    assert test[2].input_file == "title1.mkv"
    assert test[2].output_file == "tmp/title1.dpg"


def test_multiple_relative_inputs_absolute_output() -> None:
    test = list(sorted(create_task_list(
        {
            "title1.mkv",
            "foo/title2.mp4",
            "bar/title3.mp4",
        },
        "/tmp"
    )))
    assert len(test) == 3
    assert test[0].input_file == "bar/title3.mp4"
    assert test[0].output_file == "/tmp/bar/title3.dpg"
    assert test[1].input_file == "foo/title2.mp4"
    assert test[1].output_file == "/tmp/foo/title2.dpg"
    assert test[2].input_file == "title1.mkv"
    assert test[2].output_file == "/tmp/title1.dpg"


# `output is not None, input is absolute` tests


def test_absolute_input_relative_output() -> None:
    test = list(create_task_list({"/tmp/title.mkv"}, "foo"))
    assert len(test) == 1
    assert test[0].input_file == "/tmp/title.mkv"
    assert test[0].output_file == "foo/title.dpg"


def test_absolute_input_absolute_output() -> None:
    test = list(create_task_list({"/tmp/title.mkv"}, "/foo"))
    assert len(test) == 1
    assert test[0].input_file == "/tmp/title.mkv"
    assert test[0].output_file == "/foo/title.dpg"


def test_multiple_absolute_inputs_relative_output() -> None:
    test = list(sorted(create_task_list(
        {
            "/tmp/title1.mkv",
            "/tmp/foo/title2.mp4",
            "/tmp/bar/title3.mp4",
        },
        "baz"
    )))
    assert len(test) == 3
    assert test[0].input_file == "/tmp/bar/title3.mp4"
    assert test[0].output_file == "baz/bar/title3.dpg"
    assert test[1].input_file == "/tmp/foo/title2.mp4"
    assert test[1].output_file == "baz/foo/title2.dpg"
    assert test[2].input_file == "/tmp/title1.mkv"
    assert test[2].output_file == "baz/title1.dpg"


def test_multiple_absolute_inputs_absolute_output() -> None:
    test = list(sorted(create_task_list(
        {
            "/tmp/title1.mkv",
            "/tmp/foo/title2.mp4",
            "/tmp/bar/title3.mp4",
        },
        "/baz"
    )))
    assert len(test) == 3
    assert test[0].input_file == "/tmp/bar/title3.mp4"
    assert test[0].output_file =="/baz/bar/title3.dpg"
    assert test[1].input_file == "/tmp/foo/title2.mp4"
    assert test[1].output_file == "/baz/foo/title2.dpg"
    assert test[2].input_file == "/tmp/title1.mkv"
    assert test[2].output_file == "/baz/title1.dpg"


# `output is not None, input is mixed` tests


def test_mixed_inputs_relative_output() -> None:
    with pytest.raises(ValueError):
        create_task_list({"title1.mkv", "/tmp/title2.mp4"}, "tmp")


def test_mixed_inputs_absolute_output() -> None:
    with pytest.raises(ValueError):
        create_task_list({"title1.mkv", "/tmp/title2.mp4"}, "/tmp")
