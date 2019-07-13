import datetime as dt
import unittest
import os

from context import core

FIXTURES_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "fixtures"
)


class TestCore(unittest.TestCase):
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
        with self.assertRaises(ValueError):
            core.find_most_recent_log(empty_directory)

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
