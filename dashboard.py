"""
Dashboard period helpers.

Heavy lifting (aggregation, search, summary) has been pushed into
``db.py`` so the database engine — not Python — does the work.  This
module is intentionally tiny now.
"""

from datetime import datetime, timedelta, date
from typing import Optional


def get_period_range(
    period: str,
    ref_date: Optional[date] = None,
    year: Optional[int] = None,
) -> tuple[date, date]:
    """Return (start, end) date objects for the chosen period."""
    today = ref_date or date.today()

    if period == "daily":
        return today, today

    if period == "weekly":
        start = today - timedelta(days=today.weekday())
        return start, start + timedelta(days=6)

    if period == "monthly":
        start = today.replace(day=1)
        if today.month == 12:
            end = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            end = today.replace(month=today.month + 1, day=1) - timedelta(days=1)
        return start, end

    if period == "quarterly":
        y = year or today.year
        q = (today.month - 1) // 3 if year is None else 0
        start_month = q * 3 + 1
        end_month = start_month + 2
        start = date(y, start_month, 1)
        if end_month == 12:
            end = date(y, 12, 31)
        else:
            end = date(y, end_month + 1, 1) - timedelta(days=1)
        return start, end

    if period == "yearly":
        y = year or today.year
        return date(y, 1, 1), date(y, 12, 31)

    if year:
        return date(year, 1, 1), date(year, 12, 31)
    return date(1990, 1, 1), date(2099, 12, 31)


def iso_range(period: str, year: Optional[int] = None) -> tuple[str, str]:
    s, e = get_period_range(period, year=year)
    return s.strftime("%Y-%m-%d"), e.strftime("%Y-%m-%d")