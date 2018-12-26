import unittest
from dpgv4 import count_subtitle_streams, parse_subtitle_stream_id
from .util import sample_filename

class TestSubtitles(unittest.TestCase):

    def setUp(self):
        self.inp = sample_filename("Test Image - 2141.mp4")

    def test_count_zero(self):
        self.assertEqual(count_subtitle_streams(self.inp), 0)

    def test_parse_none(self):
        self.assertIsNone(parse_subtitle_stream_id(self.inp, None))

    def test_parse_zero(self):
        self.assertEqual(parse_subtitle_stream_id(self.inp, 0), 0)

    def test_parse_negative(self):
        self.assertIsNone(parse_subtitle_stream_id(self.inp, -1))
