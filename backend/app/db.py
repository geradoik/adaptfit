"""Database helpers. Standard library only, so the schema can be tested without installing anything."""
import sqlite3
from pathlib import Path

DB_DIR = Path(__file__).resolve().parent.parent / "db"
SCHEMA_PATH = DB_DIR / "schema.sql"
SEED_PATH = DB_DIR / "seed.sql"


def connect(path: str = "adaptfit.db") -> sqlite3.Connection:
    """Open a connection with foreign keys enforced (SQLite leaves them off by default)."""
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(conn: sqlite3.Connection, with_seed: bool = True) -> None:
    """Create all tables and optionally load seed data. Safe to call repeatedly."""
    conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
    if with_seed:
        conn.executescript(SEED_PATH.read_text(encoding="utf-8"))
    conn.execute("PRAGMA foreign_keys = ON")  # executescript can reset session settings
    conn.commit()


def health(conn: sqlite3.Connection) -> dict:
    """Small report used by /api/health to prove the database is reachable and migrated."""
    tables = conn.execute(
        "SELECT COUNT(*) FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%'"
    ).fetchone()[0]
    version = conn.execute("PRAGMA user_version").fetchone()[0]
    return {"database": "ok", "tables": tables, "schema_version": version}
