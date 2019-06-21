from dpgv4 import file_size
from .util import sample_filename

def test_zero_filesize() -> None:
    with open(sample_filename("file_size_1"), "rb") as inp:
        assert file_size(inp) == 0

def test_123_filesize() -> None:
    with open(sample_filename("file_size_2"), "rb") as inp:
        assert file_size(inp) == 123
