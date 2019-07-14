import datetime as dt
import gzip
import os
import re

from collections import defaultdict, namedtuple
from operator import attrgetter


LOG_FILENAME_PATTERN = re.compile(r"^nginx-access-ui\.log-(\d{8})\.(gz|log)$")
LOG_REQUEST_PATTERN = re.compile(r"^.+\[.+\] \"(.+)\" \d{3}.+ (\d+\.\d+)\n$")

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


def _most_recent_filename(filenames):
    """Finds the most recent filename in specified iterable of filenames.

    Parameters
    ----------
    filenames : Iterable[str]
        Log filenames.

    Returns
    -------
    str
        The most recent log filename.
    """

    valid_ui_logs = filter(LOG_FILENAME_PATTERN.match, filenames)

    try:
        most_recent_filename = max(valid_ui_logs)
    except ValueError:
        return None

    return most_recent_filename


def find_most_recent_log(directory):
    """Finds most recent log in specified directory.

    Parameters
    ----------
    directory : str
        Path to directory with logs.

    Returns
    -------
    LogFile
        Named tuple with full path, date and extension of
        the most recent log.
    """
    if not os.path.isdir(directory):
        raise TypeError("{0} is not a directory.".format(directory))

    most_recent_filename = _most_recent_filename(os.listdir(directory))

    if most_recent_filename is None:
        raise ValueError("There are no valid logs.")

    raw_date, extension = LOG_FILENAME_PATTERN.search(
        most_recent_filename
    ).groups()

    return LogFile(
        path=os.path.abspath(os.path.join(directory, most_recent_filename)),
        date=dt.datetime.strptime(raw_date, "%Y%m%d"),
        extension=extension,
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
