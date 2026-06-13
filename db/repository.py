"""Database repository implementation."""

from __future__ import annotations

import threading
from typing import Iterable, Iterator, Optional

from config import get_db_path
from db.schema import init_schema, setup_fts, get_db_connection
from db.filters import to_iso, parse_time, build_where_clause
from db.aggregates import (
    aggregate_summary as _agg_summary,
    aggregate_by_day as _agg_by_day,
    aggregate_by_task as _agg_by_task,
    aggregate_rate_buckets as _agg_rate_buckets,
)


class Database:
    """Singleton SQLite wrapper for tracker entries."""

    _instance: "Database | None" = None
    _ready: bool = False

    _SORT_MAP = {
        "id": "id",
        "task": "task_name", "task_name": "task_name",
        "date": "date_iso", "date_iso": "date_iso",
        "start": "start_time", "end": "end_time",
        "minutes": "total_minutes", "total_minutes": "total_minutes",
        "rate": "rate", "total": "total",
        "mode": "mode", "notes": "notes",
    }

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        if Database._ready:
            return
        Database._ready = True

        self.db_path = str(get_db_path())
        self.version: int = 0
        self._fts_available: bool = False

        self._local = threading.local()
        self._version_lock = threading.Lock()

        self._years_cache: list[int] | None = None
        self._years_cache_version: int = -1

        init_schema(self)
        setup_fts(self)

    def _get_conn(self):
        return get_db_connection(self)

    def _bump(self) -> None:
        with self._version_lock:
            self.version += 1
            self._years_cache = None

    def _build_where(self, **filters) -> tuple[str, list]:
        filters["fts_available"] = self._fts_available
        return build_where_clause(**filters)

    def add_entry(
        self, task_name, date_str, start_time, end_time,
        total_minutes, rate, total, mode="hourly", notes="",
    ) -> int:
        conn = self._get_conn()
        cur = conn.execute(
            """INSERT INTO entries
               (task_name,date,date_iso,start_time,end_time,
                total_minutes,rate,total,mode,notes)
               VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (task_name, date_str, to_iso(date_str),
             start_time or "", end_time or "",
             total_minutes, rate, total, mode, notes),
        )
        conn.commit()
        self._bump()
        return cur.lastrowid

    def update_entry(self, entry_id: int, **fields) -> None:
        if not fields:
            return
        allowed = {
            "task_name", "date", "start_time", "end_time",
            "total_minutes", "rate", "total", "mode", "notes",
        }
        cols = [f"{k}=?" for k in fields if k in allowed]
        vals = [fields[k] for k in fields if k in allowed]
        if not cols:
            return
        if "date" in fields:
            cols.append("date_iso=?")
            vals.append(to_iso(fields["date"]))
        vals.append(entry_id)
        conn = self._get_conn()
        conn.execute(f"UPDATE entries SET {','.join(cols)} WHERE id=?", vals)
        conn.commit()
        self._bump()

    def delete_entry(self, entry_id: int) -> None:
        conn = self._get_conn()
        conn.execute("DELETE FROM entries WHERE id=?", (entry_id,))
        conn.commit()
        self._bump()

    def get_entry(self, entry_id: int) -> Optional[dict]:
        row = self._get_conn().execute(
            "SELECT * FROM entries WHERE id=?", (entry_id,),
        ).fetchone()
        return dict(row) if row else None

    @staticmethod
    def calc_total_minutes(start_time: str, end_time: str) -> float:
        s, e = parse_time(start_time), parse_time(end_time)
        if s is None or e is None:
            return 0.0
        delta = (e - s).total_seconds() / 60.0
        if delta < 0:
            delta += 1440.0
        return round(delta, 2)

    @staticmethod
    def calc_total(total_minutes: float, rate: float, mode: str) -> float:
        if mode == "hourly":
            return round((total_minutes / 60.0) * rate, 2)
        return round(total_minutes * rate, 2)

    @staticmethod
    def format_hours_minutes(total_minutes: float) -> str:
        h, m = int(total_minutes // 60), int(total_minutes % 60)
        return f"{h} Hour(s) + {m} minute(s)"

    def query_entries(
        self,
        *,
        year=None, mode=None, search=None,
        start_iso=None, end_iso=None,
        sort_col="date_iso", sort_desc=True,
        limit=None, offset=0,
    ) -> list[dict]:
        where, params = self._build_where(
            year=year, mode=mode, search=search,
            start_iso=start_iso, end_iso=end_iso,
        )
        col = self._SORT_MAP.get(sort_col, "date_iso")
        direction = "DESC" if sort_desc else "ASC"
        sql = (f"SELECT * FROM entries WHERE {where} "
               f"ORDER BY {col} {direction}, id {direction}")
        if limit is not None:
            sql += " LIMIT ? OFFSET ?"
            params = params + [limit, offset]
        rows = self._get_conn().execute(sql, params).fetchall()
        return [dict(r) for r in rows]

    def count_entries(self, **filters) -> int:
        where, params = self._build_where(**filters)
        return int(self._get_conn().execute(
            f"SELECT COUNT(*) FROM entries WHERE {where}", params,
        ).fetchone()[0])

    def iter_all_entries(self, **filters) -> Iterator[dict]:
        where, params = self._build_where(**filters)
        cur = self._get_conn().execute(
            f"SELECT * FROM entries WHERE {where} "
            f"ORDER BY date_iso DESC, id DESC", params,
        )
        while True:
            batch = cur.fetchmany(500)
            if not batch:
                break
            for row in batch:
                yield dict(row)

    def get_distinct_years(self) -> list[int]:
        if (self._years_cache is not None
                and self._years_cache_version == self.version):
            return self._years_cache
        rows = self._get_conn().execute(
            "SELECT DISTINCT substr(date_iso,1,4) AS y FROM entries "
            "WHERE date_iso != '' AND date_iso != '0000-00-00' "
            "ORDER BY y DESC"
        ).fetchall()
        out: list[int] = []
        for r in rows:
            try:
                out.append(int(r["y"]))
            except (ValueError, TypeError):
                pass
        self._years_cache = out
        self._years_cache_version = self.version
        return out

    def get_distinct_dates(self, year: Optional[int] = None) -> list:
        if year is not None:
            rows = self._get_conn().execute(
                "SELECT DISTINCT date FROM entries "
                "WHERE date_iso BETWEEN ? AND ? "
                "ORDER BY date_iso",
                [f"{year:04d}-01-01", f"{year:04d}-12-31"]
            ).fetchall()
        else:
            rows = self._get_conn().execute(
                "SELECT DISTINCT date FROM entries "
                "WHERE date_iso != '' AND date_iso != '0000-00-00' "
                "ORDER BY date_iso"
            ).fetchall()
        return [r["date"] for r in rows]

    def aggregate_summary(self, **filters) -> dict:
        where, params = self._build_where(**filters)
        return _agg_summary(self._get_conn(), where, params)

    def aggregate_by_day(self, **filters) -> list[dict]:
        where, params = self._build_where(**filters)
        return _agg_by_day(self._get_conn(), where, params)

    def aggregate_by_task(self, limit: int = 10, **filters) -> list[dict]:
        where, params = self._build_where(**filters)
        return _agg_by_task(self._get_conn(), where, params, limit)

    def aggregate_rate_buckets(self, **filters) -> list[dict]:
        where, params = self._build_where(**filters)
        return _agg_rate_buckets(self._get_conn(), where, params)

    def sum_total(self, **filters) -> float:
        where, params = self._build_where(**filters)
        r = self._get_conn().execute(
            f"SELECT COALESCE(SUM(total), 0.0) FROM entries WHERE {where}",
            params,
        ).fetchone()
        return float(r[0]) if r else 0.0

    def bulk_insert(
        self, entries: list[dict],
        progress_callback=None, batch_size: int = 500,
    ) -> int:
        if not entries:
            return 0
        conn = self._get_conn()
        inserted = 0
        total = len(entries)
        sql = ("INSERT INTO entries"
               " (task_name,date,date_iso,start_time,end_time,"
               "  total_minutes,rate,total,mode,notes)"
               " VALUES (?,?,?,?,?,?,?,?,?,?)")
        try:
            for i in range(0, total, batch_size):
                chunk = entries[i:i + batch_size]
                data = [(
                    e.get("task_name", ""),
                    e.get("date", ""),
                    to_iso(e.get("date", "")),
                    e.get("start_time", ""),
                    e.get("end_time", ""),
                    e.get("total_minutes", 0),
                    e.get("rate", 0),
                    e.get("total", 0),
                    e.get("mode", "hourly"),
                    e.get("notes", ""),
                ) for e in chunk]
                conn.executemany(sql, data)
                inserted += len(chunk)
                if progress_callback:
                    try:
                        progress_callback(inserted, total)
                    except Exception:
                        pass
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        if inserted:
            self._bump()
        return inserted

    def recalculate_all(self) -> int:
        conn = self._get_conn()
        cur = conn.execute("""
            UPDATE entries
               SET total = ROUND(
                       CASE WHEN mode='hourly'
                            THEN total_minutes/60.0 * rate
                            ELSE total_minutes * rate END, 2)
             WHERE ABS(total - ROUND(
                       CASE WHEN mode='hourly'
                            THEN total_minutes/60.0 * rate
                            ELSE total_minutes * rate END, 2)) > 0.005
        """)
        affected = cur.rowcount
        conn.commit()
        if affected and affected > 0:
            self._bump()
        return max(affected, 0)

    def adjust_entry_time(
        self, entry_id: int, adjustment_minutes: float, reason: str = "",
    ) -> Optional[dict]:
        entry = self.get_entry(entry_id)
        if entry is None:
            return None
        new_minutes = max(entry["total_minutes"] + adjustment_minutes, 0)
        new_total = self.calc_total(new_minutes, entry["rate"], entry["mode"])
        tag = f"Adjusted {adjustment_minutes:+.0f} min"
        if reason:
            tag += f": {reason}"
        sep = " | " if entry.get("notes") else ""
        self.update_entry(
            entry_id,
            total_minutes=new_minutes, total=new_total,
            notes=(entry.get("notes") or "") + sep + tag,
        )
        return self.get_entry(entry_id)

    def clear_all_entries(self) -> int:
        conn = self._get_conn()
        n = conn.execute("SELECT COUNT(*) FROM entries").fetchone()[0]
        conn.execute("DELETE FROM entries")
        conn.execute("DELETE FROM sqlite_sequence WHERE name='entries'")
        if self._fts_available:
            try:
                conn.execute("INSERT INTO entries_fts(entries_fts) VALUES('rebuild')")
            except Exception:
                pass
        conn.commit()
        self._bump()
        return int(n)