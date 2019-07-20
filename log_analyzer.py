#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" Log Analyzer

The program is supposed to be used to analyze Nginx access logs in
the predefined format.

Example of allowed log names:
* nginx-access-ui.log-20170630.gz
* nginx-access-ui.log-20170630.log

"""

import datetime as dt
import gzip
import json
import logging
import os
import re
import sys

from argparse import ArgumentParser
from collections import defaultdict, namedtuple
from operator import attrgetter
from string import Template

try:
    from ConfigParser import SafeConfigParser
except ImportError:
    from configparser import SafeConfigParser


DEFAULT_CONFIG = {
    "REPORT_SIZE": 1000,
    "REPORT_DIR": "./reports",
    "LOG_DIR": "./log",
    "ALLOWED_INVALID_RECORDS_PART": 0.2,
    "LOGGING": "INFO",
}

DEFAULT_CONFIG_FILE_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "config.ini")
)

LOG_FILENAME_PATTERN = re.compile(r"^nginx-access-ui\.log-(\d{8})\.(gz|log)$")
LOG_REQUEST_PATTERN = re.compile(r"^.+\[.+\] \"(.+)\" \d{3}.+ (\d+\.\d+)\n$")

TEMPLATE = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "templates", "report.html")
)


LogFile = namedtuple("LogFile", ["path", "date", "extension"])
LogRequest = namedtuple("LogRequest", ["url", "time"])
LogStat = namedtuple(
    "LogStat",
    [
        "url",
        "count",
        "count_perc",
        "time_sum",
        "time_perc",
        "time_avg",
        "time_max",
        "time_med",
    ],
)


def init_config():
    """Parses arguments and config parameters.
    """
    parser = ArgumentParser(__doc__)
    parser.add_argument(
        "--config",
        help="Path to config file.",
        default=DEFAULT_CONFIG_FILE_PATH,
    )
    args = parser.parse_args()

    config = SafeConfigParser(defaults=DEFAULT_CONFIG)
    config.read(args.config)

    logging_level = config.get("main", "logging")
    logging.basicConfig(
        level=getattr(logging, logging_level, "INFO"),
        format="[%(asctime)s] %(levelname).1s %(message)s",
        datefmt="%Y.%m.%d %H:%M:%S",
    )

    return config


def main():
    """Entry point to the log analyzer programm.
    """
    config = init_config()

    report_dir = config.get("main", "REPORT_DIR")
    if not os.path.exists(report_dir):
        os.makedirs(report_dir)

    log_dir = config.get("main", "LOG_DIR")
    most_recent_log = find_most_recent_log(log_dir)

    if most_recent_log is None:
        logging.info("There are no valid logs in the directory.")
        sys.exit()

    logging.debug(
        "Found the most recent log-file {0}.".format(most_recent_log.path)
    )

    report_filename = most_recent_log.date.strftime("report-%Y.%m.%d.html")
    if os.path.exists(os.path.join(report_dir, report_filename)):
        msg = "Report for %Y.%m.%d already exists."
        logging.info(most_recent_log.date.strftime(msg))
        sys.exit()

    report_size = config.getint("main", "REPORT_SIZE")
    allowed_invalid_records_part = config.getfloat(
        "main", "ALLOWED_INVALID_RECORDS_PART"
    )

    request_stats = get_request_stats(
        most_recent_log,
        count=report_size,
        allowed_invalid_part=allowed_invalid_records_part,
    )

    if not request_stats:
        logging.info(
            "The most recent log file ({0}) has no valid records.".format(
                most_recent_log.path
            )
        )
        sys.exit()

    write_report(request_stats, to=os.path.join(report_dir, report_filename))
    logging.debug("Report has been successfully generated.")


def find_most_recent_log(directory):
    """Finds most recent log in specified directory.

    Parameters
    ----------
    directory : str
        Path to directory with logs.

    Returns
    -------
    Optional[LogFile]
        Named tuple with full path, date and extension of
        the most recent log.

    Raises
    ------
    TypeError
        Invalid directory.
    """
    if not os.path.isdir(directory):
        raise TypeError("Can't find {0} directory with logs".format(directory))

    most_recent_date = None
    most_recent_filename = None
    most_recent_ext = None

    for filename in os.listdir(directory):
        search = LOG_FILENAME_PATTERN.search(filename)
        if search is None:
            continue

        raw_date, extension = search.groups()
        try:
            date = dt.datetime.strptime(raw_date, "%Y%m%d")
        except ValueError:
            continue

        if most_recent_date is None or date > most_recent_date:
            most_recent_date = date
            most_recent_filename = filename
            most_recent_ext = extension

    if most_recent_date is None:
        return None

    return LogFile(
        path=os.path.abspath(os.path.join(directory, most_recent_filename)),
        date=most_recent_date,
        extension=most_recent_ext,
    )


def _iterate_over_requests(log):
    """Yields requested URL for each record in specified log-file.

    Parameters
    ----------
    log : LogFile
        Named tuple that describes log-file.

    Yields
    -------
    Optional[LogRequest]
        LogRequest instance or None (for invalid rows).

    Raises
    ------
    ValueError
        If log-file has invalid extension.
    IOError
        Could not open the log-file.
    """
    if log.extension not in {"log", "gz"}:
        raise ValueError("Invalid extension of the log-file.")

    open_method = open if log.extension == "log" else gzip.open

    with open_method(log.path, "rb") as f:
        for line in f:
            line = line.decode("utf-8")
            search = LOG_REQUEST_PATTERN.search(line)

            if search is None:
                yield None
                continue

            try:
                method, url, protocol = search.group(1).split()
            except ValueError:
                # Invalid $request format
                yield None
                continue

            time = float(search.group(2))

            yield LogRequest(url, time)


def _median(sorted_list):
    """Returns median value for specified sorted list.

    Parameters
    ----------
    arr: List[float]

    Returns
    -------
    float
    """
    assert sorted_list, "List is empty"

    n_items = len(sorted_list)
    return 0.5 * (sorted_list[(n_items - 1) // 2] + sorted_list[n_items // 2])


def _aggregate_stats_by_url(log, allowed_invalid_part=0.2):
    """Aggregates time statistics for requests in specified log-file.

    Parameters
    ----------
    log : LogFile
        Named tuple that describes log-file.
    allowed_invalid_part: float
        Allowed part of invalid rows in the log-file.

    Returns
    -------
    Tuple[float, float, Dict[str, List[float]]]
        Number of valid rows,
        Overall time,
        Times for each requested URL.

    Raises
    ------
    ValueError
        If `allowed_invalid_part` is exceeded.
    ValueError
        If log-file has invalid extension.
    IOError
        Could not open the log-file.
    """

    count_valid = 0.0
    count_invalid = 0.0

    time_valid = 0.0
    times = defaultdict(list)

    for request in _iterate_over_requests(log):
        if request is None:
            count_invalid += 1
            continue

        count_valid += 1
        time_valid += request.time
        times[request.url].append(request.time)

    count_all = (count_invalid + count_valid) or 1.0
    if count_invalid / count_all > allowed_invalid_part:
        raise ValueError("Too many invalid rows in the log-file.")

    return count_valid, time_valid, times


def get_request_stats(log, count=1000, allowed_invalid_part=0.2):
    """Returns a list with statistical data for each requested URL.

    Parameters
    ----------
    log: LogFile
        Named tuple that describes log-file.
    count: int
        Return stats for `count` URLs
    allowed_invalid_part: float
        Allowed part of invalid rows in the log-file.

    Returns
    -------
    List[LogStat]
        List of statistics for each requested URL sorted by `time_sum`

    Raises
    ------
    ValueError
        If `allowed_invalid_part` is exceeded.
    ValueError
        If log-file has invalid extension.
    IOError
        Could not open the log-file.
    """

    count_valid, time_all, times = _aggregate_stats_by_url(
        log, allowed_invalid_part
    )

    stats = []

    for url in times:
        url_count = len(times[url])
        url_sorted_times = sorted(times[url])
        url_time_sum = sum(times[url])

        url_stat = LogStat(
            url=url,
            count=url_count,
            count_perc=(100 * url_count / count_valid),
            time_sum=url_time_sum,
            time_perc=(100 * url_time_sum / time_all),
            time_avg=(url_time_sum / url_count),
            time_max=url_sorted_times[-1],
            time_med=_median(url_sorted_times),
        )
        stats.append(url_stat)

    return sorted(stats, key=attrgetter("time_sum"), reverse=True)[:count]


def _render(stats):
    """Renders the default template with calculated stats.

    Parameters
    ----------
    stats: List[LogStat]
        List of statistics for each URL.

    Returns
    -------
    str
        String representation of rendered template
    """
    with open(TEMPLATE, "rb") as f:
        template = Template(f.read().decode("utf-8"))

    return template.safe_substitute(
        table_json=json.dumps([record._asdict() for record in stats])
    )


def write_report(stats, to):
    """Writes rendered report to specified file.

    Parameters
    ----------
    stats: List[LogStat]
        List of statistics for each URL.
    to: str
        Path to write report.

    Raises
    ------
    IOError
        Unable to write file
    """
    rendered_template = _render(stats)

    with open(to, "wb") as f:
        f.write(rendered_template.encode("utf-8"))


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logging.info("Terminated...")
    except Exception as exc:
        logging.exception(exc)
