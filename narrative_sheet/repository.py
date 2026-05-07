"""Repository and file-storage helpers for the local document library."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import re
import sqlite3
import uuid

from .classifier import category_label, suggest_category
from .database import DEFAULT_DATABASE_PATH, connect
from .exporters import export_docx, export_xlsx
from .parser import parse_markdown

DEFAULT_STORAGE_DIR = Path("storage")


@dataclass(frozen=True)
class Document:
    """A document record stored in SQLite."""

    id: int
    title: str
    category: str
    tags: str
    source_filename: str
    markdown_path: Path
    docx_path: Path
    xlsx_path: Path
    is_deleted: bool
    created_at: str
    updated_at: str
    deleted_at: str | None

    @property
    def category_label(self) -> str:
        return category_label(self.category)


def create_document(
    markdown: str,
    source_filename: str,
    *,
    title: str | None = None,
    category: str | None = None,
    tags: str = "",
    database_path: str | Path = DEFAULT_DATABASE_PATH,
    storage_dir: str | Path = DEFAULT_STORAGE_DIR,
) -> Document:
    """Create a document record, save Markdown, and generate Word/Excel files."""

    document_title = (title or _title_from_markdown(markdown) or Path(source_filename).stem).strip()
    document_category = category or suggest_category(document_title, markdown, source_filename)
    paths = _new_document_paths(source_filename, storage_dir)
    paths["markdown"].write_text(markdown, encoding="utf-8")
    _regenerate_files(paths["markdown"], paths["docx"], paths["xlsx"], source_filename)

    now = _now()
    with connect(database_path) as connection:
        cursor = connection.execute(
            """
            INSERT INTO documents (
                title, category, tags, source_filename, markdown_path, docx_path,
                xlsx_path, is_deleted, created_at, updated_at, deleted_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, 0, ?, ?, NULL)
            """,
            (
                document_title,
                document_category,
                tags.strip(),
                source_filename,
                _relative_storage_path(paths["markdown"], storage_dir),
                _relative_storage_path(paths["docx"], storage_dir),
                _relative_storage_path(paths["xlsx"], storage_dir),
                now,
                now,
            ),
        )
        connection.commit()
        return get_document(cursor.lastrowid, database_path=database_path, storage_dir=storage_dir)


def get_document(
    document_id: int,
    *,
    database_path: str | Path = DEFAULT_DATABASE_PATH,
    storage_dir: str | Path = DEFAULT_STORAGE_DIR,
    include_deleted: bool = False,
) -> Document:
    """Load a single document by id."""

    sql = "SELECT * FROM documents WHERE id = ?"
    params: list[object] = [document_id]
    if not include_deleted:
        sql += " AND is_deleted = 0"
    with connect(database_path) as connection:
        row = connection.execute(sql, params).fetchone()
    if row is None:
        raise KeyError(f"Document not found: {document_id}")
    return _row_to_document(row, storage_dir)


def list_documents(
    *,
    search_title: str = "",
    category: str = "all",
    database_path: str | Path = DEFAULT_DATABASE_PATH,
    storage_dir: str | Path = DEFAULT_STORAGE_DIR,
) -> list[Document]:
    """List active documents with optional title search and category filter."""

    clauses = ["is_deleted = 0"]
    params: list[object] = []
    if search_title.strip():
        clauses.append("title LIKE ?")
        params.append(f"%{search_title.strip()}%")
    if category and category != "all":
        clauses.append("category = ?")
        params.append(category)

    sql = f"SELECT * FROM documents WHERE {' AND '.join(clauses)} ORDER BY updated_at DESC, id DESC"
    with connect(database_path) as connection:
        rows = connection.execute(sql, params).fetchall()
    return [_row_to_document(row, storage_dir) for row in rows]


def update_document(
    document_id: int,
    *,
    title: str,
    category: str,
    tags: str,
    markdown: str,
    database_path: str | Path = DEFAULT_DATABASE_PATH,
    storage_dir: str | Path = DEFAULT_STORAGE_DIR,
) -> Document:
    """Update metadata and Markdown, then regenerate Word/Excel files."""

    document = get_document(document_id, database_path=database_path, storage_dir=storage_dir)
    document.markdown_path.write_text(markdown, encoding="utf-8")
    _regenerate_files(document.markdown_path, document.docx_path, document.xlsx_path, document.source_filename)
    now = _now()
    with connect(database_path) as connection:
        connection.execute(
            """
            UPDATE documents
               SET title = ?, category = ?, tags = ?, updated_at = ?
             WHERE id = ? AND is_deleted = 0
            """,
            (title.strip() or document.source_filename, category, tags.strip(), now, document_id),
        )
        connection.commit()
    return get_document(document_id, database_path=database_path, storage_dir=storage_dir)


def soft_delete_document(
    document_id: int,
    *,
    database_path: str | Path = DEFAULT_DATABASE_PATH,
) -> None:
    """Mark a document as deleted without removing files from disk."""

    now = _now()
    with connect(database_path) as connection:
        connection.execute(
            "UPDATE documents SET is_deleted = 1, deleted_at = ?, updated_at = ? WHERE id = ?",
            (now, now, document_id),
        )
        connection.commit()


def read_markdown(document: Document) -> str:
    """Read the current Markdown content from local storage."""

    return document.markdown_path.read_text(encoding="utf-8")


def _row_to_document(row: sqlite3.Row, storage_dir: str | Path) -> Document:
    root = Path(storage_dir)
    return Document(
        id=int(row["id"]),
        title=row["title"],
        category=row["category"],
        tags=row["tags"],
        source_filename=row["source_filename"],
        markdown_path=root / row["markdown_path"],
        docx_path=root / row["docx_path"],
        xlsx_path=root / row["xlsx_path"],
        is_deleted=bool(row["is_deleted"]),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        deleted_at=row["deleted_at"],
    )


def _new_document_paths(source_filename: str, storage_dir: str | Path) -> dict[str, Path]:
    root = Path(storage_dir)
    markdown_dir = root / "markdown"
    docx_dir = root / "word"
    xlsx_dir = root / "excel"
    for directory in (markdown_dir, docx_dir, xlsx_dir):
        directory.mkdir(parents=True, exist_ok=True)

    stem = _safe_stem(Path(source_filename).stem)
    token = uuid.uuid4().hex[:8]
    basename = f"{stem}-{token}"
    return {
        "markdown": markdown_dir / f"{basename}.md",
        "docx": docx_dir / f"{basename}.docx",
        "xlsx": xlsx_dir / f"{basename}.xlsx",
    }


def _regenerate_files(markdown_path: Path, docx_path: Path, xlsx_path: Path, source_filename: str) -> None:
    rows = parse_markdown(markdown_path.read_text(encoding="utf-8"), source_file=source_filename)
    export_docx(rows, docx_path)
    export_xlsx(rows, xlsx_path)


def _relative_storage_path(path: Path, storage_dir: str | Path) -> str:
    return path.relative_to(Path(storage_dir)).as_posix()


def _title_from_markdown(markdown: str) -> str:
    for line in markdown.splitlines():
        stripped = line.strip()
        if stripped.startswith("# "):
            return stripped.removeprefix("# ").strip()
    return ""


def _safe_stem(value: str) -> str:
    safe = re.sub(r"[^0-9A-Za-z\u4e00-\u9fff_-]+", "_", value).strip("_")
    return safe or "document"


def _now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
