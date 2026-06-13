"""Database query filters and utilities."""

from __future__ import annotations

import re
from datetime import datetime
from typing import Optional


def to_iso(date_str: str) -> str:
    """Convert date string to ISO format."""
    if not date_str:
        return "0000-00-00"
    for fmt in ("%Y-%m-%d", "%m/%d/%y", "%m/%d/%Y", "%m-%d-%y", "%m-%d-%Y"):
        try:
            return datetime.strptime(date_str.strip(), fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return "0000-00-00"


def parse_time(time_str: str) -> Optional[datetime]:
    """Parse time string into datetime object."""
    time_str = time_str.strip()
    if not time_str:
        return None
    for fmt in (
        "%I:%M:%S %p", "%I:%M %p", "%I:%M:%S%p", "%I:%M%p",
        "%H:%M:%S", "%H:%M",
    ):
        try:
            return datetime.strptime(time_str, fmt)
        except ValueError:
            continue
    return None


_FTS_TOKEN = re.compile(r"\w+", re.UNICODE)


def fts_query(text: str) -> Optional[str]:
    """Build a safe FTS5 prefix-match query string."""
    tokens = _FTS_TOKEN.findall(text or "")
    if not tokens:
        return None
    return " ".join(f"{t}*" for t in tokens)


def build_where_clause(
    *,
    year: Optional[int] = None,
    mode: Optional[str] = None,
    search: Optional[str] = None,
    start_iso: Optional[str] = None,
    end_iso: Optional[str] = None,
    fts_available: bool = False,
) -> tuple[str, list]:
    """Build WHERE clause and parameters for entry queries."""
    clauses = ["1=1"]
    params: list = []

    if year is not None:
        clauses.append("date_iso BETWEEN ? AND ?")
        params.extend([f"{year:04d}-01-01", f"{year:04d}-12-31"])

    if mode and mode.lower() not in ("all", ""):
        clauses.append("mode=?")
        params.append(mode)

    if start_iso:
        clauses.append("date_iso >= ?")
        params.append(start_iso)
    if end_iso:
        clauses.append("date_iso <= ?")
        params.append(end_iso)

    if search:
        search = search.strip()
        if search:
            if fts_available:
                q = fts_query(search)
                like = f"%{search}%"
                if q:
                    clauses.append(
                        "(id IN (SELECT rowid FROM entries_fts "
                        "WHERE entries_fts MATCH ?) OR date LIKE ?)"
                    )
                    params.extend([q, like])
                else:
                    clauses.append("date LIKE ?")
                    params.append(like)
            else:
                like = f"%{search.lower()}%"
                clauses.append(
                    "(LOWER(task_name) LIKE ? "
                    " OR LOWER(notes) LIKE ? "
                    " OR date LIKE ?)"
                )
                params.extend([like, like, f"%{search}%"])

    return " AND ".join(clauses), params