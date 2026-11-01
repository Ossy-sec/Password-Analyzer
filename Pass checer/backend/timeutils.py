"""
All timestamps in this app are UTC, stored as "YYYY-MM-DD HH:MM:SS" text.
That fixed format sorts and compares correctly as plain strings in SQL.
"""

from datetime import datetime, timedelta, timezone

FORMAT = "%Y-%m-%d %H:%M:%S"


def utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def utc_now_iso() -> str:
    return utc_now().strftime(FORMAT)


def iso(dt: datetime) -> str:
    return dt.strftime(FORMAT)


def parse_iso(text: str) -> datetime:
    return datetime.strptime(text, FORMAT)


def seconds_ago_iso(seconds: float) -> str:
    return iso(utc_now() - timedelta(seconds=seconds))
