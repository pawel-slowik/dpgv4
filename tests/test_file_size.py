import unittest
from dpgv4 import file_size
from .util import sample_filename

class TestFileSize(unittest.TestCase):

    def test_zero_filesize(self) -> None:
        with open(sample_filename("file_size_1"), "rb") as inp:
            self.assertEqual(file_size(inp), 0)

    def test_123_filesize(self) -> None:
        with open(sample_filename("file_size_2"), "rb") as inp:
            self.assertEqual(file_size(inp), 123)
