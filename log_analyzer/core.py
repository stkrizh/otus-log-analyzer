import datetime as dt
import os
import re

from collections import namedtuple


LOG_FILENAME_PATTERN = re.compile(r"^nginx-access-ui\.log-(\d{8})\.(gz|log)$")


LogFile = namedtuple("LogFile", ["path", "date", "extension"])


def _most_recent_log(filenames):
    """Finds the most recent filename in specified list of filenames.

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
