# pylint: disable=missing-docstring
from io import BytesIO
from dpgv4 import parse_progress_total, parse_progress_current, read_progress


def test_progress_total() -> None:
    line = "  Duration: 01:01:01.01, start: 0.000000, bitrate: 592 kb/s"
    assert parse_progress_total(line) == 3661.01


def test_progress_current() -> None:
    line = (
        "frame=  269 fps=0.0 q=2.0 size=     256kB time=00:00:11.12 "
        "bitrate= 188.5kbits/s dup=0 drop=65 speed=22.2x    "
    )
    assert parse_progress_current(line) == 11.12


def test_progress_current_none() -> None:
    line = "  Duration: 01:01:01.01, start: 0.000000, bitrate: 592 kb/s"
    assert parse_progress_current(line) is None


def test_read_progress_without_errors() -> None:
    total_line = b"  Duration: 01:01:01.01, start: 0.000000, bitrate: 592 kb/s"
    current_line = (
        b"frame=  269 fps=0.0 q=2.0 size=     256kB time=00:00:11.12 "
        b"bitrate= 188.5kbits/s dup=0 drop=65 speed=22.2x    "
    )
    stream = BytesIO(total_line + b"\n" + current_line)
    assert read_progress("label", stream) == ""


def test_read_progress_with_error() -> None:
    total_line = b"  Duration: 01:01:01.01, start: 0.000000, bitrate: 592 kb/s"
    current_line = (
        b"frame=  269 fps=0.0 q=2.0 size=     256kB time=00:00:11.12 "
        b"bitrate= 188.5kbits/s dup=0 drop=65 speed=22.2x    "
    )
    error_line = b" some error message! "
    stream = BytesIO(total_line + b"\n" + error_line + b"\n" + current_line)
    assert read_progress("label", stream) == " some error message! \n"
