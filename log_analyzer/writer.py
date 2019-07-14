import json
import os

from string import Template


TEMPLATE = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "templates", "report.html")
)


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


def write(stats, to):
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
