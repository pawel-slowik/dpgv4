from dpgv4 import get_aspect_ratio
from .util import sample_filename

def test_aspect_ratio() -> None:
    input_filename = sample_filename("Test Image - 2141.mp4")
    assert get_aspect_ratio(input_filename) == 4 / 3
