import unittest
from dpgv4 import create_task_list

class TestTaskFilenames(unittest.TestCase):

    # one-to-one, a special case

    def test_one_input_one_output(self) -> None:
        self.assertEqual(
            create_task_list({"input.mp4"}, "output.dpg"),
            [("input.mp4", "output.dpg")]
        )

    # `output is None` tests

    def test_relative_input_no_output(self) -> None:
        self.assertEqual(
            create_task_list({"title.mkv"}, None),
            [("title.mkv", "title.dpg")]
        )

    def test_absolute_input_no_output(self) -> None:
        self.assertEqual(
            create_task_list({"/tmp/title.mkv"}, None),
            [("/tmp/title.mkv", "/tmp/title.dpg")]
        )

    def test_mixed_inputs_no_output(self) -> None:
        self.assertEqual(
            sorted(create_task_list({
                "title1.mp4",
                "/tmp/title2.mkv",
            }, None)),
            sorted([
                ("title1.mp4", "title1.dpg"),
                ("/tmp/title2.mkv", "/tmp/title2.dpg"),
            ])
        )

    # `output is not None, input is relative` tests

    def test_relative_input_relative_output(self) -> None:
        self.assertEqual(
            create_task_list({"title.mkv"}, "tmp"),
            [("title.mkv", "tmp/title.dpg")]
        )

    def test_relative_input_absolute_output(self) -> None:
        self.assertEqual(
            create_task_list({"title.mkv"}, "/tmp"),
            [("title.mkv", "/tmp/title.dpg")]
        )

    def test_multiple_relative_inputs_relative_output(self) -> None:
        self.assertEqual(
            sorted(create_task_list({
                "title1.mkv",
                "foo/title2.mp4",
                "bar/title3.mp4",
            }, "tmp")),
            sorted([
                ("title1.mkv", "tmp/title1.dpg"),
                ("foo/title2.mp4", "tmp/foo/title2.dpg"),
                ("bar/title3.mp4", "tmp/bar/title3.dpg"),
            ])
        )

    def test_multiple_relative_inputs_absolute_output(self) -> None:
        self.assertEqual(
            sorted(create_task_list({
                "title1.mkv",
                "foo/title2.mp4",
                "bar/title3.mp4",
            }, "/tmp")),
            sorted([
                ("title1.mkv", "/tmp/title1.dpg"),
                ("foo/title2.mp4", "/tmp/foo/title2.dpg"),
                ("bar/title3.mp4", "/tmp/bar/title3.dpg"),
            ])
        )

    # `output is not None, input is absolute` tests

    def test_absolute_input_relative_output(self) -> None:
        self.assertEqual(
            create_task_list({"/tmp/title.mkv"}, "foo"),
            [("/tmp/title.mkv", "foo/title.dpg")]
        )

    def test_absolute_input_absolute_output(self) -> None:
        self.assertEqual(
            create_task_list({"/tmp/title.mkv"}, "/foo"),
            [("/tmp/title.mkv", "/foo/title.dpg")]
        )

    def test_multiple_absolute_inputs_relative_output(self) -> None:
        self.assertEqual(
            sorted(create_task_list({
                "/tmp/title1.mkv",
                "/tmp/foo/title2.mp4",
                "/tmp/bar/title3.mp4",
            }, "baz")),
            sorted([
                ("/tmp/title1.mkv", "baz/title1.dpg"),
                ("/tmp/foo/title2.mp4", "baz/foo/title2.dpg"),
                ("/tmp/bar/title3.mp4", "baz/bar/title3.dpg"),
            ])
        )

    def test_multiple_absolute_inputs_absolute_output(self) -> None:
        self.assertEqual(
            sorted(create_task_list({
                "/tmp/title1.mkv",
                "/tmp/foo/title2.mp4",
                "/tmp/bar/title3.mp4",
            }, "/baz")),
            sorted([
                ("/tmp/title1.mkv", "/baz/title1.dpg"),
                ("/tmp/foo/title2.mp4", "/baz/foo/title2.dpg"),
                ("/tmp/bar/title3.mp4", "/baz/bar/title3.dpg"),
            ])
        )

    # `output is not None, input is mixed` tests

    def test_mixed_inputs_relative_output(self) -> None:
        with self.assertRaises(ValueError):
            create_task_list({"title1.mkv", "/tmp/title2.mp4"}, "tmp")

    def test_mixed_inputs_absolute_output(self) -> None:
        with self.assertRaises(ValueError):
            create_task_list({"title1.mkv", "/tmp/title2.mp4"}, "/tmp")
