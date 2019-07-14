#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" Log Analyzer

The program is supposed to be used to analyze Nginx access logs in
predefined format:

'$remote_addr $remote_user $http_x_real_ip [$time_local] "$request" '
'$status $body_bytes_sent "$http_referer" '
'"$http_user_agent" "$http_x_forwarded_for" "$http_X_REQUEST_ID" "$http_X_RB_USER"
'$request_time';

Each log file has to be named as:
* nginx-access-ui.log-20170630.gz
* nginx-access-ui.log-20170630.log

"""
import os
import sys

from argparse import ArgumentParser
from configparser import SafeConfigParser, Error as ConfigError

from core import find_most_recent_log, get_request_stats
from writer import write


DEFAULT_CONFIG = {
    "REPORT_SIZE": 1000,
    "REPORT_DIR": "./reports",
    "LOG_DIR": "./log",
    "ALLOWED_INVALID_RECORDS_PART": 0.2,
}

DEFAULT_CONFIG_FILE_PATH = os.path.abspath(
    os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.ini")
)


def _get_parameters():
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

    report_size = config.getint("main", "REPORT_SIZE")
    allowed_invalid_records_part = config.getfloat(
        "main", "ALLOWED_INVALID_RECORDS_PART"
    )
    report_dir = config.get("main", "report_dir")
    log_dir = config.get("main", "log_dir")

    return report_size, allowed_invalid_records_part, report_dir, log_dir


def main():
    """Entry point to the log analyzer programm.
    """
    try:
        report_size, allowed_invalid_records_part, report_dir, log_dir = (
            _get_parameters()
        )
    except UnicodeDecodeError:
        print("Invald encoding")
        sys.exit()
    except ValueError as exc:
        print(exc)
        sys.exit()
    except ConfigError as exc:
        print(exc)
        sys.exit()

    print(report_size)
    print(allowed_invalid_records_part)
    print(report_dir)
    print(log_dir)

    most_recent_log = find_most_recent_log(log_dir)
    print(most_recent_log)


if __name__ == "__main__":
    main()
