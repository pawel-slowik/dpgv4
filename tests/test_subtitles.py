import unittest
from dpgv4 import count_subtitle_streams, parse_subtitle_stream_id, subtitle_options
from .util import sample_filename

class TestSubtitles(unittest.TestCase):

    def setUp(self) -> None:
        self.inp = sample_filename("Test Image - 2141.mp4")

    def test_count_zero(self) -> None:
        self.assertEqual(count_subtitle_streams(self.inp), 0)

    def test_parse_none(self) -> None:
        self.assertIsNone(parse_subtitle_stream_id(self.inp, None))

    def test_parse_zero(self) -> None:
        self.assertEqual(parse_subtitle_stream_id(self.inp, 0), 0)

    def test_parse_negative(self) -> None:
        self.assertIsNone(parse_subtitle_stream_id(self.inp, -1))

    def test_parse_external(self) -> None:
        self.assertEqual(parse_subtitle_stream_id(sample_filename("World - 2.mp4"), None), 0)

    def test_options_no_external_none(self) -> None:
        input_filename = sample_filename("Test Image - 2141.mp4")
        self.assertEqual(subtitle_options(input_filename, None, None), [])

    def test_options_no_external_zero(self) -> None:
        input_filename = sample_filename("Test Image - 2141.mp4")
        input_index = 0
        expected_filename = input_filename
        expected_index = 0
        options = list(subtitle_options(input_filename, input_index, None))
        self.assertGreaterEqual(len(options), 2)
        self.assertIn(expected_filename, options[1])
        self.assertIn("stream_index=%d" % expected_index, options[1])

    def test_options_no_external_one(self) -> None:
        input_filename = sample_filename("Test Image - 2141.mp4")
        input_index = 1
        expected_filename = input_filename
        expected_index = 1
        options = list(subtitle_options(input_filename, input_index, None))
        self.assertGreaterEqual(len(options), 2)
        self.assertIn(expected_filename, options[1])
        self.assertIn("stream_index=%d" % expected_index, options[1])

    def test_options_external_none(self) -> None:
        input_filename = sample_filename("World - 2.mp4")
        self.assertEqual(subtitle_options(input_filename, None, None), [])

    def test_options_external_zero(self) -> None:
        input_filename = sample_filename("World - 2.mp4")
        input_index = 0
        expected_filename = sample_filename("World - 2.srt")
        expected_index = 0
        options = list(subtitle_options(input_filename, input_index, None))
        self.assertGreaterEqual(len(options), 2)
        self.assertIn(expected_filename, options[1])
        self.assertIn("stream_index=%d" % expected_index, options[1])

    def test_options_external_one(self) -> None:
        input_filename = sample_filename("World - 2.mp4")
        input_index = 1
        expected_filename = input_filename
        expected_index = 0
        options = list(subtitle_options(input_filename, input_index, None))
        self.assertGreaterEqual(len(options), 2)
        self.assertIn(expected_filename, options[1])
        self.assertIn("stream_index=%d" % expected_index, options[1])
