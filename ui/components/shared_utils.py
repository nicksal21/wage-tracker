"""Shared utility functions."""

from __future__ import annotations

from typing import Optional
from datetime import date, datetime


def format_currency(value: float, symbol: str = "$") -> str:
    return f"{symbol}{float(value or 0):,.2f}"


def format_rate(value: float, symbol: str = "$") -> str:
    return f"{symbol}{float(value or 0):,.2f}/hr"


def format_hours(value: float) -> str:
    return f"{float(value or 0):.1f} hrs"


def format_int(value) -> str:
    return f"{int(value or 0):,}"


def format_float0(value: float) -> str:
    return f"{float(value or 0):,.0f}"


def format_float2(value: float) -> str:
    return f"{float(value or 0):,.2f}"


def format_value(kind: str, value, symbol: str = "$") -> str:
    if kind == "currency":
        return format_currency(value, symbol)
    if kind == "rate":
        return format_rate(value, symbol)
    if kind == "hours":
        return format_hours(value)
    if kind == "int":
        return format_int(value)
    if kind == "float0":
        return format_float0(value)
    if kind == "float2":
        return format_float2(value)
    return str(value)


def parse_date(date_str: str) -> Optional[date]:
    if not date_str:
        return None
    for fmt in ("%Y-%m-%d", "%m/%d/%y", "%m/%d/%Y", "%m-%d-%y", "%m-%d-%Y"):
        try:
            return datetime.strptime(date_str.strip(), fmt).date()
        except ValueError:
            continue
    return None


def to_iso_date(date_str: str) -> str:
    if not date_str:
        return "0000-00-00"
    d = parse_date(date_str)
    if d:
        return d.strftime("%Y-%m-%d")
    return "0000-00-00"


def month_name(month_num: int) -> str:
    names = ["January", "February", "March", "April", "May", "June",
             "July", "August", "September", "October", "November", "December"]
    return names[month_num - 1] if 1 <= month_num <= 12 else ""