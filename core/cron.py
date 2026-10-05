"""Minimal cron expression matching (minute hour day month weekday)."""

from __future__ import annotations

from datetime import datetime


def _field_matches(field: str, current: int) -> bool:
    if field == "*":
        return True
    if field.startswith("*/"):
        try:
            return current % int(field[2:]) == 0
        except (ValueError, ZeroDivisionError):
            return False
    if "-" in field and "/" not in field:
        try:
            start, end = field.split("-")
            return int(start) <= current <= int(end)
        except ValueError:
            return False
    if "," in field:
        try:
            return current in [int(v.strip()) for v in field.split(",")]
        except ValueError:
            return False
    try:
        return int(field) == current
    except ValueError:
        return False


def matches_now(cron_expr: str, now: datetime | None = None) -> bool:
    now = now or datetime.now()
    parts = cron_expr.strip().split()
    if len(parts) != 5:
        return False
    minute, hour, day, month, weekday = parts
    cron_weekday = (now.weekday() + 1) % 7  # Python 0=Monday -> cron 0=Sunday
    return (
        _field_matches(minute, now.minute)
        and _field_matches(hour, now.hour)
        and _field_matches(day, now.day)
        and _field_matches(month, now.month)
        and _field_matches(weekday, cron_weekday)
    )
