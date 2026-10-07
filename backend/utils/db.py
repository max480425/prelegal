"""SQLite database access for the users table.

The database file is created on first use and the schema is idempotent
(``CREATE TABLE IF NOT EXISTS``), so application startup always yields a
usable database. The Docker container deletes the file before boot so the
database is created from scratch on every container start.
"""

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional

from backend.utils.config import get_settings


def _connect() -> sqlite3.Connection:
    """Open a connection to the application database."""
    db_path = get_settings().database_path
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Create the schema if it does not exist. Safe to call repeatedly."""
    with _connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL UNIQUE COLLATE NOCASE,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.commit()


def create_user(email: str, password_hash: str) -> Dict:
    """Insert a new user and return the created row.

    Raises:
        sqlite3.IntegrityError: if the email is already registered.
    """
    created_at = datetime.now(timezone.utc).isoformat()
    with _connect() as conn:
        cursor = conn.execute(
            "INSERT INTO users (email, password_hash, created_at) VALUES (?, ?, ?)",
            (email, password_hash, created_at),
        )
        conn.commit()
        user_id = cursor.lastrowid
        return {
            "id": user_id,
            "email": email,
            "created_at": created_at,
        }


def get_user_by_email(email: str) -> Optional[Dict]:
    """Look up a user by email (case-insensitive)."""
    with _connect() as conn:
        row = conn.execute(
            "SELECT id, email, password_hash, created_at FROM users WHERE email = ?",
            (email,),
        ).fetchone()
        return dict(row) if row else None


def get_user_by_id(user_id: int) -> Optional[Dict]:
    """Look up a user by id."""
    with _connect() as conn:
        row = conn.execute(
            "SELECT id, email, created_at FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()
        return dict(row) if row else None


def clear_users() -> None:
    """Delete all users. Used by tests to isolate state."""
    with _connect() as conn:
        conn.execute("DELETE FROM users")
        conn.commit()
