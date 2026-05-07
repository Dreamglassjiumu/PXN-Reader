"""SQLite database setup for the local Streamlit document library."""

from __future__ import annotations

import sqlite3
from pathlib import Path

DEFAULT_DATA_DIR = Path("data")
DEFAULT_DATABASE_PATH = DEFAULT_DATA_DIR / "pxn_reader.sqlite3"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    category TEXT NOT NULL DEFAULT 'other',
    tags TEXT NOT NULL DEFAULT '',
    source_filename TEXT NOT NULL,
    markdown_path TEXT NOT NULL,
    docx_path TEXT NOT NULL,
    xlsx_path TEXT NOT NULL,
    is_deleted INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    deleted_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_documents_active_updated
    ON documents (is_deleted, updated_at DESC);

CREATE INDEX IF NOT EXISTS idx_documents_category
    ON documents (category);
"""


def connect(database_path: str | Path = DEFAULT_DATABASE_PATH) -> sqlite3.Connection:
    """Open a SQLite connection and ensure the schema exists."""

    path = Path(database_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    initialize(connection)
    return connection


def initialize(connection: sqlite3.Connection) -> None:
    """Create or update the local database schema."""

    connection.executescript(_SCHEMA)
    connection.commit()
