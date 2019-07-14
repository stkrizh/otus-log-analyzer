import datetime as dt
import unittest
import os

from context import core

FIXTURES_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "fixtures"
)


class TestCore(unittest.TestCase):
    def setUp(self):
        log_path = os.path.abspath(
            os.path.join(
                FIXTURES_PATH,
                "valid_filenames",
                "nginx-access-ui.log-20190102.log",
            )
        )
        self.log = core.LogFile(
            path=log_path,
            date=dt.datetime.strptime("20190102", "%Y%m%d"),
            extension="log",
        )

        self.invalid_extension_log = core.LogFile(
            path=log_path,
            date=dt.datetime.strptime("20190102", "%Y%m%d"),
            extension="bz",
        )

        invalid_log_path = os.path.abspath(
            os.path.join(
                FIXTURES_PATH,
                "valid_filenames",
                "nginx-access-ui.log-20180101.log",
            )
        )
        self.invalid_log = core.LogFile(
            path=invalid_log_path,
            date=dt.datetime.strptime("20180101", "%Y%m%d"),
            extension="log",
        )

        empty_log_path = os.path.abspath(
            os.path.join(
                FIXTURES_PATH,
                "valid_filenames",
                "nginx-access-ui.log-20170101.log",
            )
        )
        self.empty_log = core.LogFile(
            path=empty_log_path,
            date=dt.datetime.strptime("20170101", "%Y%m%d"),
            extension="log",
        )

        encoding_log_path = os.path.abspath(
            os.path.join(
                FIXTURES_PATH,
                "valid_filenames",
                "nginx-access-ui.log-20160101.log",
            )
        )
        self.encoding_log = core.LogFile(
            path=encoding_log_path,
            date=dt.datetime.strptime("20160101", "%Y%m%d"),
            extension="log",
        )

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

    def test_iterate_over_requests_invalid_extension(self):
        with self.assertRaises(ValueError):
            list(core._iterate_over_requests(self.invalid_extension_log))

    def test_iterate_over_requests(self):
        self.assertEqual(
            4,
            sum(
                request is None
                for request in core._iterate_over_requests(self.log)
            ),
        )

    def test_aggregate_stats_by_url(self):
        count_valid, time_all, times = core._aggregate_stats_by_url(
            self.log, 0.4
        )

        self.assertEqual(8, count_valid)
        self.assertAlmostEqual(3.4, time_all)
        self.assertEqual(6, len(times["/api/bbb"]))

    def test_aggregate_stats_by_url_part_invalid(self):
        with self.assertRaises(ValueError):
            core._aggregate_stats_by_url(self.log)

    def test_get_request_stats_part_invalid(self):
        with self.assertRaises(ValueError):
            core.get_request_stats(self.log)

    def test_get_request_stats_count(self):
        self.assertEqual(0, len(core.get_request_stats(self.log, 0, 0.5)))
        self.assertEqual(1, len(core.get_request_stats(self.log, 1, 0.5)))
        self.assertEqual(2, len(core.get_request_stats(self.log, 2, 0.5)))
        self.assertEqual(3, len(core.get_request_stats(self.log, 3, 0.5)))

    def test_get_request_stats(self):
        stats = core.get_request_stats(self.log, allowed_invalid_part=0.5)

        self.assertEqual("/api/bbb", stats[0].url)
        self.assertEqual(6, stats[0].count)
        self.assertAlmostEqual(0.5, stats[0].time_med)
        self.assertAlmostEqual(0.8, stats[0].time_max)
        self.assertAlmostEqual(0.5, stats[0].time_avg)
        self.assertAlmostEqual(3.0, stats[0].time_sum)
        self.assertAlmostEqual(100 * (3.0 / 3.4), stats[0].time_perc)
        self.assertAlmostEqual(75, stats[0].count_perc)

    def test_get_request_stats_invalid_file(self):
        with self.assertRaises(ValueError):
            core.get_request_stats(self.invalid_log, allowed_invalid_part=0.5)

    def test_get_request_stats_empty_file(self):
        self.assertEqual(
            [],
            core.get_request_stats(self.empty_log, allowed_invalid_part=0.5)
        )

    def test_get_request_stats_encoding_file(self):
        with self.assertRaises(UnicodeDecodeError):
            core.get_request_stats(self.encoding_log, 0.5)
