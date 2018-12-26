import unittest
from dpgv4 import get_duration
from .util import sample_filename

class TestDuration(unittest.TestCase):

    def test_duration(self):
        input_filename = sample_filename("Test Image - 2141.mp4")
        self.assertEqual(get_duration(input_filename), 30.03)
