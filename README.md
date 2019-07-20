# otus-log-analyzer
Log Analyzer task for Otus

## Installation

```
git clone https://github.com/stkrizh/otus-log-analyzer.git
cd otus-log-analyzer
make test
```

## Examples

Use default configuration file:
```
python -m log_analyzer
```

Use custom configuration file:
```
python -m log_analyzer --config /path/to/config.ini
```

Example configuration:
```
[main]
ALLOWED_INVALID_RECORDS_PART=0.2
REPORT_SIZE=1000
REPORT_DIR=./reports
LOG_DIR=./log
LOGGING=INFO
```

## Compatibility
Python 2.7+
