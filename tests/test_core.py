import datetime as dt
import unittest
import os

from context import core

FIXTURES_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "fixtures"
)


class TestCore(unittest.TestCase):
    def test_is_valid_date(self):
        self.assertTrue(core._is_valid_date("20190606"))
        self.assertTrue(core._is_valid_date("10001010"))
        self.assertTrue(core._is_valid_date("20200229"))

        self.assertFalse(core._is_valid_date("20190631"))
        self.assertFalse(core._is_valid_date("_20180606"))
        self.assertFalse(core._is_valid_date("20190606_"))

    def test_median(self):
        with self.assertRaises(AssertionError):
            core._median([])

        self.assertEqual(1, core._median([1]))
        self.assertEqual(1, core._median([1, 1, 1]))
        self.assertEqual(4, core._median([1, 4, 4, 4, 1]))
        self.assertEqual(3.5, core._median([1, 2, 3, 4, 5, 6]))

    def test_most_recent_filenames(self):
        filenames = [
            "nginx-access-ui.log-20170630.gz",
            "nginx-access-ui.log-20150629.gz",
            "nginx-access-ui.log-20150630.bz",
            "image.jpg",
            "nginx-access-ui.log-20150630.gz",
            "nginx-access-ui.log-20170701.log",
            "nginx-access-ui.log-20170701.gz",
            "nginx-access-XX.log-20191212.gz",
        ]

        self.assertEqual(
            "nginx-access-ui.log-20170701.log",
            core._most_recent_filename(filenames),
        )

    def test_invalid_logs_directory(self):
        invalid_path = os.path.join(FIXTURES_PATH, "foobar")
        with self.assertRaises(TypeError):
            core.find_most_recent_log(invalid_path)

    def test_empty_directory(self):
        empty_directory = os.path.join(FIXTURES_PATH, "empty_directory")
        self.assertIs(None, core.find_most_recent_log(empty_directory))

    def test_find_most_recent_log(self):
        logs_directory = os.path.join(FIXTURES_PATH, "valid_filenames")
        expected_path = os.path.join(
            logs_directory, "nginx-access-ui.log-20190102.log"
        )
        expected_date = dt.datetime(2019, 1, 2)

        actual_path, actual_date, actual_ext = core.find_most_recent_log(
            logs_directory
        )

        self.assertEqual(expected_path, actual_path)
        self.assertEqual(expected_date, actual_date)
        self.assertEqual("log", actual_ext)
