import datetime as dt
import gzip
import os
import re

from collections import namedtuple


LOG_FILENAME_PATTERN = re.compile(r"^nginx-access-ui\.log-(\d{8})\.(gz|log)$")
LOG_REQUEST_PATTERN = re.compile(r"^.+\[.+\] \"(.+)\" \d{3}.+ (\d+\.\d+)\n$")

LogFile = namedtuple("LogFile", ["path", "date", "extension"])
LogRequest = namedtuple("LogRequest", ["url", "time"])


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
        Named tuple that describes log-file

    Yields
    -------
    Optional[LogRequest]
        LogRequest instance or None (for invalid rows)

    Raises
    ------
    ValueError
        If log-file has invalid extension
    IOError
        Could not open the log-file
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
