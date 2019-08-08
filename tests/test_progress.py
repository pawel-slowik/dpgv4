# pylint: disable=missing-docstring
from dpgv4 import parse_progress_total, parse_progress_current

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
