"""Database connection management."""

from __future__ import annotations

import sqlite3
import threading
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from db.repository import Database


def get_db_connection(db_instance: "Database") -> sqlite3.Connection:
    """Return a thread-local SQLite connection."""
    conn = getattr(db_instance._local, "conn", None)
    if conn is not None:
        return conn
    
    conn = sqlite3.connect(db_instance.db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA temp_store=MEMORY")
    conn.execute("PRAGMA cache_size=-65536")
    db_instance._local.conn = conn
    return conn