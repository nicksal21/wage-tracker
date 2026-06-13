"""
Handles all theme and tax configurations.
Persists settings to a JSON file in the user's home directory.

The parsed config is cached in memory; ``load_config`` returns the same
dict across calls until ``save_config`` is invoked (or the process is
restarted).
"""

import json
from pathlib import Path
from typing import Any

CONFIG_DIR = Path("./.freelance_tracker")
CONFIG_FILE = CONFIG_DIR / "config.json"
DB_FILE = CONFIG_DIR / "tracker.db"

DEFAULT_CONFIG: dict[str, Any] = {
    "theme": {
        "mode": "dark",
        "primary_color": "#1f6aa5",
        "secondary_color": "#2d2d2d",
        "accent_color": "#3b8ed0",
        "text_color": "#DCE4EE",
        "bg_color": "#1a1a1a",
        "card_bg": "#2b2b2b",
        "sidebar_bg": "#1f1f1f",
        "success_color": "#28a745",
        "warning_color": "#ffc107",
        "danger_color": "#dc3545",
        "chart_colors": [
            "#3b8ed0", "#28a745", "#ffc107", "#dc3545",
            "#9b59b6", "#e67e22", "#1abc9c", "#e74c3c",
        ],
    },
    "tax": {
        "filing_status": "single",
        "state": "CA",
        "tax_year": 2024,
        "deductions": {
            "use_standard": True,
            "custom_deduction": 0.0,
            "business_expenses": 0.0,
            "health_insurance": 0.0,
            "retirement_contributions": 0.0,
            "home_office": 0.0,
            "other_deductions": 0.0,
        },
    },
    "general": {
        "default_rate": 0.0,
        "default_mode": "hourly",
        "currency_symbol": "$",
        "page_size": 100,
        "search_debounce_ms": 300,
    },
}

US_STATES = {
    "AL": "Alabama", "AK": "Alaska", "AZ": "Arizona", "AR": "Arkansas",
    "CA": "California", "CO": "Colorado", "CT": "Connecticut",
    "DE": "Delaware", "DC": "District of Columbia", "FL": "Florida",
    "GA": "Georgia", "HI": "Hawaii", "ID": "Idaho", "IL": "Illinois",
    "IN": "Indiana", "IA": "Iowa", "KS": "Kansas", "KY": "Kentucky",
    "LA": "Louisiana", "ME": "Maine", "MD": "Maryland", "MA": "Massachusetts",
    "MI": "Michigan", "MN": "Minnesota", "MS": "Mississippi", "MO": "Missouri",
    "MT": "Montana", "NE": "Nebraska", "NV": "Nevada", "NH": "New Hampshire",
    "NJ": "New Jersey", "NM": "New Mexico", "NY": "New York",
    "NC": "North Carolina", "ND": "North Dakota", "OH": "Ohio",
    "OK": "Oklahoma", "OR": "Oregon", "PA": "Pennsylvania",
    "RI": "Rhode Island", "SC": "South Carolina", "SD": "South Dakota",
    "TN": "Tennessee", "TX": "Texas", "UT": "Utah", "VT": "Vermont",
    "VA": "Virginia", "WA": "Washington", "WV": "West Virginia",
    "WI": "Wisconsin", "WY": "Wyoming",
}

FILING_STATUSES = {
    "single": "Single",
    "married_jointly": "Married Filing Jointly",
    "married_separately": "Married Filing Separately",
    "head_of_household": "Head of Household",
}

# ---------------------------------------------------------------- internal
_config_cache: dict | None = None
_config_version: int = 0


def _deep_merge(base: dict, override: dict) -> dict:
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def ensure_config_dir() -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)


def _read_from_disk() -> dict:
    ensure_config_dir()
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r") as f:
                return _deep_merge(DEFAULT_CONFIG, json.load(f))
        except (json.JSONDecodeError, IOError):
            pass
    return _deep_merge(DEFAULT_CONFIG, {})


def load_config() -> dict:
    """Return the cached config dict (avoid mutating in place; use save_config)."""
    global _config_cache
    if _config_cache is None:
        _config_cache = _read_from_disk()
    return _config_cache


def save_config(config: dict) -> None:
    global _config_cache, _config_version
    ensure_config_dir()
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)
    _config_cache = config
    _config_version += 1


def get_config_version() -> int:
    """Monotonically increments every time the config is saved."""
    return _config_version


def get_db_path() -> Path:
    ensure_config_dir()
    return DB_FILE