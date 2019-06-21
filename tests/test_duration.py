from dpgv4 import get_duration
from .util import sample_filename

def test_duration() -> None:
    input_filename = sample_filename("Test Image - 2141.mp4")
    assert get_duration(input_filename) == 30.03
