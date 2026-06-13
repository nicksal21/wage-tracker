"""Dashboard specifications and constants."""

from __future__ import annotations


PERIODS = ["Daily", "Weekly", "Monthly", "Quarterly", "Yearly", "All-Time"]

CHARTS = [
    "Earnings Over Time", "Hours Over Time", "Task Distribution",
    "Cumulative Earnings", "Rate Distribution",
]

CHART_KEYS = [
    "earnings_over_time", "hours_over_time", "task_distribution",
    "cumulative_earnings", "rate_distribution",
]

CARDS = [
    ("Total Earned",  "total_earned",   "currency"),
    ("Hours Worked",  "total_hours",    "hours"),
    ("Entries",       "total_entries",  "int"),
    ("Eff. Rate",     "effective_rate", "rate"),
    ("Days Worked",   "days_worked",    "int"),
    ("Tasks Done",    "total_tasks",    "float0"),
]

STAT_ROWS = [
    ("EARNINGS",                 None,                       None),
    ("Total Earned",             "total_earned",             "currency"),
    ("Average per Entry",        "avg_earning_per_entry",    "currency"),
    ("Median per Entry",         "median_earning_per_entry", "currency"),
    ("Std Dev (Earnings)",       "stdev_earnings",           "currency"),
    ("Min Entry Earning",        "min_earning",              "currency"),
    ("Max Entry Earning",        "max_earning",              "currency"),
    ("Avg Daily Earning",        "avg_daily_earning",        "currency"),
    ("Median Daily Earning",     "median_daily_earning",     "currency"),
    ("TIME",                     None,                       None),
    ("Total Hours",              "total_hours",              "float2"),
    ("Avg Daily Hours",          "avg_daily_hours",          "float2"),
    ("Total Minutes",            "total_minutes",            "float0"),
    ("RATES",                    None,                       None),
    ("Effective Rate",           "effective_rate",           "rate"),
    ("Avg Hourly Rate",          "avg_hourly_rate",          "currency"),
    ("Median Hourly Rate",       "median_hourly_rate",       "currency"),
    ("Std Dev (Rate)",           "stdev_hourly_rate",        "currency"),
    ("Min Hourly Rate",          "min_hourly_rate",          "currency"),
    ("Max Hourly Rate",          "max_hourly_rate",          "currency"),
    ("GENERAL",                  None,                       None),
    ("Total Entries",            "total_entries",            "int"),
    ("  Hourly Entries",         "hourly_entries",           "int"),
    ("  Per-Task Entries",       "per_task_entries",         "int"),
    ("Tasks Completed",          "total_tasks",              "float0"),
    ("Days Worked",              "days_worked",              "int"),
    ("Busiest Day",              "_busiest",                 "busiest"),
]

PAGE_SIZES = ["50", "100", "250", "500", "1000"]