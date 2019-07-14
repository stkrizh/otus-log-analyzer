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

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname).1s %(message)s",
    datefmt="%Y.%m.%d %H:%M:%S",
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
        logging.error("Only UTF-8 is allowed encoding for config file.")
        sys.exit()
    except ConfigError as exc:
        logging.error("Config file is invalid.")
        sys.exit()
    except ValueError as exc:
        logging.error("Error in the config file: " + str(exc))
        sys.exit()
    except Exception:
        logging.exception("Unexpected error with parameters: ")
        sys.exit()

    if not os.path.exists(report_dir):
        try:
            os.makedirs(report_dir)
        except OSError:
            logging.error("Unable to create report directory.")
            sys.exit()
        except Exception:
            logging.exception("Unexpected error with report directory: ")
            sys.exit()

    try:
        most_recent_log = find_most_recent_log(log_dir)
    except TypeError:
        logging.error("Invalid log directory.")
        sys.exit()
    except Exception:
        logging.exception("Unexpected error with the most recent log search: ")
        sys.exit()

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

    try:
        request_stats = get_request_stats(
            most_recent_log,
            count=report_size,
            allowed_invalid_part=allowed_invalid_records_part,
        )
    except ValueError:
        logging.info(
            "Allowed invalid records part ({0}) is exceeded.".format(
                allowed_invalid_records_part
            )
        )
        sys.exit()
    except KeyboardInterrupt:
        logging.info("Stats processing has been interrupted.")
        sys.exit()
    except Exception:
        logging.exception("Unexpected error with stats processing.")
        sys.exit()

    if not request_stats:
        logging.info(
            "The most recent log file ({0}) has no valid records.".format(
                most_recent_log.path
            )
        )
        sys.exit()

    try:
        write(request_stats, to=os.path.join(report_dir, report_filename))
    except IOError:
        logging.error("Unable to write report.")
    except Exception:
        logging.exception("Unexpected error: ")

    logging.debug("Report has been successfully generated.")


if __name__ == "__main__":
    main()
