# pylint: disable=missing-docstring
from dpgv4 import process_args_str

def test_process_args_str() -> None:
    assert process_args_str("ffmpeg arg1 arg2") == "ffmpeg arg1 arg2"

def test_process_args_bytes() -> None:
    assert "ffmpeg arg1 arg2" in process_args_str(b"ffmpeg arg1 arg2")

def test_process_args_str_sequence() -> None:
    assert process_args_str(["ffmpeg", "arg1", "arg2"]) == "ffmpeg arg1 arg2"

def test_process_args_bytes_sequence() -> None:
    assert "ffmpeg arg1 arg2" in process_args_str([b"ffmpeg", b"arg1", b"arg2"])
