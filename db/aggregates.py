"""Database aggregation functions."""

from __future__ import annotations

import math
import statistics
import sqlite3


def _stdev_from_moments(sum_sq: float, mean: float, n: int) -> float:
    if n < 2:
        return 0.0
    var = sum_sq / n - mean * mean
    if var < 0:
        var = 0.0
    return math.sqrt(var * n / (n - 1))


def _empty_summary() -> dict:
    return {
        "total_entries": 0, "hourly_entries": 0, "per_task_entries": 0,
        "total_earned": 0.0, "total_hours": 0.0, "total_minutes": 0.0,
        "total_tasks": 0.0, "effective_rate": 0.0,
        "avg_hourly_rate": 0.0, "median_hourly_rate": 0.0,
        "min_hourly_rate": 0.0, "max_hourly_rate": 0.0,
        "stdev_hourly_rate": 0.0,
        "avg_earning_per_entry": 0.0, "median_earning_per_entry": 0.0,
        "min_earning": 0.0, "max_earning": 0.0, "stdev_earnings": 0.0,
        "avg_daily_earning": 0.0, "median_daily_earning": 0.0,
        "avg_daily_hours": 0.0, "days_worked": 0,
        "busiest_day": "N/A", "busiest_day_earning": 0.0,
    }


def sql_median(conn: sqlite3.Connection, where: str, params: list, col: str) -> float:
    cnt = conn.execute(
        f"SELECT COUNT(*) FROM entries WHERE {where} AND {col} IS NOT NULL",
        params,
    ).fetchone()[0]
    if cnt == 0:
        return 0.0
    if cnt % 2 == 1:
        r = conn.execute(
            f"SELECT {col} FROM entries WHERE {where} "
            f"AND {col} IS NOT NULL ORDER BY {col} LIMIT 1 OFFSET ?",
            params + [cnt // 2],
        ).fetchone()
        return float(r[0]) if r else 0.0
    rs = conn.execute(
        f"SELECT {col} FROM entries WHERE {where} "
        f"AND {col} IS NOT NULL ORDER BY {col} LIMIT 2 OFFSET ?",
        params + [cnt // 2 - 1],
    ).fetchall()
    return (float(rs[0][0]) + float(rs[1][0])) / 2 if len(rs) == 2 else 0.0


def aggregate_summary(conn: sqlite3.Connection, where: str, params: list) -> dict:
    row = conn.execute(f"""
        SELECT
            COUNT(*)                                                      AS n,
            SUM(CASE WHEN mode='hourly'   THEN 1 ELSE 0 END)             AS n_hr,
            SUM(CASE WHEN mode='per_task' THEN 1 ELSE 0 END)             AS n_pt,
            COALESCE(SUM(total), 0.0)                                    AS earned,
            COALESCE(SUM(CASE WHEN mode='hourly'   THEN total_minutes ELSE 0 END),0.0) AS hr_min,
            COALESCE(SUM(CASE WHEN mode='per_task' THEN total_minutes ELSE 0 END),0.0) AS tasks,
            COUNT(DISTINCT date_iso)                                     AS days,
            COALESCE(MIN(total), 0.0)                                    AS min_e,
            COALESCE(MAX(total), 0.0)                                    AS max_e,
            COALESCE(AVG(total), 0.0)                                    AS avg_e,
            COALESCE(SUM(total*total), 0.0)                              AS sum_e_sq,
            COALESCE(MIN(CASE WHEN mode='hourly' AND rate>0 THEN rate END), 0.0)        AS min_r,
            COALESCE(MAX(CASE WHEN mode='hourly' AND rate>0 THEN rate END), 0.0)        AS max_r,
            COALESCE(AVG(CASE WHEN mode='hourly' AND rate>0 THEN rate END), 0.0)        AS avg_r,
            COALESCE(SUM(CASE WHEN mode='hourly' AND rate>0 THEN rate*rate ELSE 0 END), 0.0) AS sum_r_sq,
            SUM(CASE WHEN mode='hourly' AND rate>0 THEN 1 ELSE 0 END)    AS n_r
        FROM entries WHERE {where}
    """, params).fetchone()

    n = row["n"] or 0
    if n == 0:
        return _empty_summary()

    day_rows = conn.execute(f"""
        SELECT SUM(total) AS d_total,
               SUM(CASE WHEN mode='hourly' THEN total_minutes ELSE 0 END)/60.0 AS d_hours,
               date_iso, date
        FROM entries WHERE {where}
        GROUP BY date_iso
    """, params).fetchall()
    day_totals = [r["d_total"] or 0.0 for r in day_rows]
    day_hours = [r["d_hours"] or 0.0 for r in day_rows]
    if day_rows:
        busiest = max(day_rows, key=lambda r: r["d_total"] or 0.0)
        busiest_day = busiest["date"] or busiest["date_iso"] or "N/A"
        busiest_earning = float(busiest["d_total"] or 0.0)
    else:
        busiest_day, busiest_earning = "N/A", 0.0

    median_e = sql_median(conn, where, params, "total")
    median_r = sql_median(
        conn, f"{where} AND mode='hourly' AND rate>0", params, "rate",
    )
    median_daily = statistics.median(day_totals) if day_totals else 0.0

    avg_e = row["avg_e"] or 0.0
    avg_r = row["avg_r"] or 0.0
    n_r = row["n_r"] or 0
    stdev_e = _stdev_from_moments(row["sum_e_sq"] or 0.0, avg_e, n)
    stdev_r = _stdev_from_moments(row["sum_r_sq"] or 0.0, avg_r, n_r)

    total_hours = (row["hr_min"] or 0.0) / 60.0
    effective_rate = ((row["earned"] or 0.0) / total_hours
                       if total_hours > 0 else 0.0)

    return {
        "total_entries":          n,
        "hourly_entries":         row["n_hr"] or 0,
        "per_task_entries":       row["n_pt"] or 0,
        "total_earned":           row["earned"] or 0.0,
        "total_hours":            total_hours,
        "total_minutes":          row["hr_min"] or 0.0,
        "total_tasks":            row["tasks"] or 0.0,
        "effective_rate":         effective_rate,
        "avg_hourly_rate":        avg_r,
        "median_hourly_rate":     median_r,
        "min_hourly_rate":        row["min_r"] or 0.0,
        "max_hourly_rate":        row["max_r"] or 0.0,
        "stdev_hourly_rate":      stdev_r,
        "avg_earning_per_entry":  avg_e,
        "median_earning_per_entry": median_e,
        "min_earning":            row["min_e"] or 0.0,
        "max_earning":            row["max_e"] or 0.0,
        "stdev_earnings":         stdev_e,
        "avg_daily_earning":      sum(day_totals) / len(day_totals) if day_totals else 0.0,
        "median_daily_earning":   median_daily,
        "avg_daily_hours":        sum(day_hours) / len(day_hours) if day_hours else 0.0,
        "days_worked":            row["days"] or 0,
        "busiest_day":            busiest_day,
        "busiest_day_earning":    busiest_earning,
    }


def aggregate_by_day(conn: sqlite3.Connection, where: str, params: list) -> list[dict]:
    rows = conn.execute(f"""
        SELECT date_iso, date,
               COALESCE(SUM(total), 0.0) AS total,
               COALESCE(SUM(CASE WHEN mode='hourly' THEN total_minutes ELSE 0 END), 0.0)/60.0 AS hours
        FROM entries WHERE {where}
        GROUP BY date_iso ORDER BY date_iso
    """, params).fetchall()
    return [dict(r) for r in rows]


def aggregate_by_task(conn: sqlite3.Connection, where: str, params: list, limit: int = 10) -> list[dict]:
    rows = conn.execute(f"""
        SELECT task_name, COALESCE(SUM(total), 0.0) AS total
        FROM entries WHERE {where}
        GROUP BY task_name ORDER BY total DESC LIMIT ?
    """, params + [limit]).fetchall()
    return [dict(r) for r in rows]


def aggregate_rate_buckets(conn: sqlite3.Connection, where: str, params: list) -> list[dict]:
    rng = conn.execute(f"""
        SELECT MIN(rate) AS mn, MAX(rate) AS mx
        FROM entries WHERE {where} AND mode='hourly' AND rate>0
    """, params).fetchone()
    if not rng or rng["mn"] is None:
        return []
    mn, mx = float(rng["mn"]), float(rng["mx"])
    span = max(mx - mn, 1.0)
    bucket = max(1.0, round(span / 12.0))
    rows = conn.execute(f"""
        SELECT CAST(rate / ? AS INTEGER) * ? AS bucket, COUNT(*) AS cnt
        FROM entries WHERE {where} AND mode='hourly' AND rate>0
        GROUP BY bucket ORDER BY bucket
    """, [bucket, bucket] + params).fetchall()
    return [{"bucket": float(r["bucket"]), "count": int(r["cnt"]),
              "size": bucket} for r in rows]