#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" Log Analyzer

The program is supposed to be used to analyze Nginx access logs in
the predefined format.

Example of allowed log names:
* nginx-access-ui.log-20170630.gz
* nginx-access-ui.log-20170630.log

"""
import os
import sys
import logging

from argparse import ArgumentParser
from ConfigParser import SafeConfigParser, Error as ConfigError

from core import find_most_recent_log, get_request_stats
from writer import write


DEFAULT_CONFIG = {
    "REPORT_SIZE": 1000,
    "REPORT_DIR": "./reports",
    "LOG_DIR": "./log",
    "ALLOWED_INVALID_RECORDS_PART": 0.2,
}

DEFAULT_CONFIG_FILE_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "config.ini")
)

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname).1s %(message)s",
    datefmt="%Y.%m.%d %H:%M:%S",
)


def get_config():
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

    return config


def main():
    """Entry point to the log analyzer programm.
    """
    config = get_config()

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

    report_size = config.int("main", "REPORT_SIZE")
    allowed_invalid_records_part = config.getfloat("main", "REPORT_SIZE")

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

    write(request_stats, to=os.path.join(report_dir, report_filename))
    logging.debug("Report has been successfully generated.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logging.info("Terminated...")
    except Exception:
        logging.exception()
