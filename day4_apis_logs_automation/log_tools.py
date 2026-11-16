"""Helpers for reading the application log. Used by 02_log_analysis.py and
03_escalation_report.py.

A log line looks like this:

    2026-10-14T09:10:57Z ERROR auth-service request_id=b81b319d customer_id=C003 latency_ms=24258 msg="Token validation failed: upstream timeout"
"""

import re
from collections import Counter
from datetime import datetime, timedelta

# A regular expression ("regex") is a pattern for pulling pieces out of text.
# (?P<name>...) captures a piece and gives it a name.
#   \S+  = one or more non-space characters      \w+ = letters/digits
#   \d+  = one or more digits                    .*  = anything
LOG_PATTERN = re.compile(
    r"^(?P<time>\S+) "
    r"(?P<level>\w+)\s+"
    r"(?P<service>\S+) "
    r"request_id=(?P<request_id>\w+) "
    r"customer_id=(?P<customer_id>\w+) "
    r"latency_ms=(?P<latency_ms>\d+) "
    r'msg="(?P<message>.*)"$'
)


def parse_line(line):
    """Turn one log line into a dict. Returns None if the line does not fit."""
    match = LOG_PATTERN.match(line.strip())
    if match is None:
        return None
    entry = match.groupdict()
    entry["time"] = datetime.strptime(entry["time"], "%Y-%m-%dT%H:%M:%SZ")
    entry["latency_ms"] = int(entry["latency_ms"])
    return entry


def read_log(path):
    """Read a log file. Returns (entries, number_of_lines_we_could_not_parse)."""
    entries = []
    skipped = 0
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            entry = parse_line(line)
            if entry is None:
                skipped += 1
            else:
                entries.append(entry)
    return entries, skipped


def find_incident(entries, bucket_minutes=10, error_threshold=5):
    """Find the time window where errors piled up.

    Method: count ERROR lines per 10-minute bucket. Any bucket with 5 or more
    is "hot". The incident runs from the first hot bucket to the last one.
    Returns None when there is no hot bucket.
    """
    errors = [entry for entry in entries if entry["level"] == "ERROR"]

    def bucket_start(moment):
        minute = moment.minute - moment.minute % bucket_minutes
        return moment.replace(minute=minute, second=0)

    per_bucket = Counter(bucket_start(entry["time"]) for entry in errors)
    hot = sorted(bucket for bucket, count in per_bucket.items() if count >= error_threshold)
    if not hot:
        return None

    start = hot[0]
    end = hot[-1] + timedelta(minutes=bucket_minutes)
    inside = [entry for entry in errors if start <= entry["time"] < end]
    return {
        "start": start,
        "end": end,
        "minutes": int((end - start).total_seconds() / 60),
        "error_count": len(inside),
        "top_messages": Counter(entry["message"] for entry in inside).most_common(3),
        "services": Counter(entry["service"] for entry in inside).most_common(),
        "customers_affected": len({entry["customer_id"] for entry in inside}),
    }
