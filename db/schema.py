"""Database schema and migrations."""

from __future__ import annotations

import sqlite3
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from db.repository import Database


def init_schema(db_instance: "Database") -> None:
    """Initialize the database schema."""
    conn = get_db_connection(db_instance)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS entries (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            task_name       TEXT    NOT NULL,
            date            TEXT    NOT NULL,
            date_iso        TEXT    NOT NULL DEFAULT '',
            start_time      TEXT,
            end_time        TEXT,
            total_minutes   REAL    NOT NULL,
            rate            REAL    NOT NULL,
            total           REAL    NOT NULL,
            mode            TEXT    NOT NULL DEFAULT 'hourly',
            notes           TEXT    DEFAULT ''
        )
    """)

    cols = [r[1] for r in conn.execute("PRAGMA table_info(entries)")]
    if "date_iso" not in cols:
        conn.execute(
            "ALTER TABLE entries ADD COLUMN date_iso TEXT NOT NULL DEFAULT ''"
        )
    
    from db.filters import to_iso
    missing = conn.execute(
        "SELECT id, date FROM entries WHERE date_iso='' OR date_iso IS NULL"
    ).fetchall()
    if missing:
        conn.executemany(
            "UPDATE entries SET date_iso=? WHERE id=?",
            [(to_iso(r["date"]), r["id"]) for r in missing],
        )

    conn.execute("CREATE INDEX IF NOT EXISTS idx_date_iso ON entries(date_iso)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_mode     ON entries(mode)")
    conn.commit()


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


def setup_fts(db_instance: "Database") -> None:
    """Create FTS5 virtual table + triggers."""
    conn = get_db_connection(db_instance)
    try:
        conn.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS entries_fts USING fts5(
                task_name, notes,
                content='entries', content_rowid='id'
            )
        """)
    except sqlite3.OperationalError:
        db_instance._fts_available = False
        return
    
    db_instance._fts_available = True

    conn.executescript("""
        CREATE TRIGGER IF NOT EXISTS entries_ai AFTER INSERT ON entries BEGIN
            INSERT INTO entries_fts(rowid, task_name, notes)
            VALUES (new.id, new.task_name, COALESCE(new.notes, ''));
        END;
        CREATE TRIGGER IF NOT EXISTS entries_ad AFTER DELETE ON entries BEGIN
            INSERT INTO entries_fts(entries_fts, rowid, task_name, notes)
            VALUES ('delete', old.id, old.task_name, COALESCE(old.notes, ''));
        END;
        CREATE TRIGGER IF NOT EXISTS entries_au AFTER UPDATE ON entries BEGIN
            INSERT INTO entries_fts(entries_fts, rowid, task_name, notes)
            VALUES ('delete', old.id, old.task_name, COALESCE(old.notes, ''));
            INSERT INTO entries_fts(rowid, task_name, notes)
            VALUES (new.id, new.task_name, COALESCE(new.notes, ''));
        END;
    """)

    fts_n = conn.execute("SELECT COUNT(*) FROM entries_fts").fetchone()[0]
    ent_n = conn.execute("SELECT COUNT(*) FROM entries").fetchone()[0]
    if fts_n != ent_n:
        conn.execute("DELETE FROM entries_fts")
        conn.execute(
            "INSERT INTO entries_fts(rowid, task_name, notes) "
            "SELECT id, task_name, COALESCE(notes, '') FROM entries"
        )
    conn.commit()