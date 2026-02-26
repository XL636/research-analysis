"""阅读助手存储层 - SQLite CRUD for documents, pages, chats, sessions, suggestions."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

import yaml
from loguru import logger


class ReaderStore:
    """阅读助手存储：文档元数据、分页文本、对话历史、会话、推荐问题."""

    def __init__(self, db_path: str | None = None):
        if db_path is None:
            config_path = Path("config/settings.yaml")
            if config_path.exists():
                with open(config_path, encoding="utf-8") as f:
                    config = yaml.safe_load(f)
                db_path = config.get("knowledge_base", {}).get(
                    "db_path", "./knowledge_base/research.db"
                )
            else:
                db_path = "./knowledge_base/research.db"

        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    @staticmethod
    def _beijing_now() -> str:
        return datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m-%d %H:%M:%S")

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS reader_documents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    file_name TEXT NOT NULL,
                    file_type TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    total_pages INTEGER DEFAULT 0,
                    current_page INTEGER DEFAULT 1,
                    created_at TEXT,
                    updated_at TEXT
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS reader_pages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    document_id INTEGER NOT NULL,
                    page_num INTEGER NOT NULL,
                    content TEXT NOT NULL DEFAULT '',
                    FOREIGN KEY (document_id) REFERENCES reader_documents(id) ON DELETE CASCADE,
                    UNIQUE(document_id, page_num)
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS reader_chats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    document_id INTEGER NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    page_num INTEGER DEFAULT 1,
                    created_at TEXT,
                    FOREIGN KEY (document_id) REFERENCES reader_documents(id) ON DELETE CASCADE
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS reader_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    document_id INTEGER NOT NULL,
                    title TEXT NOT NULL DEFAULT '新对话',
                    created_at TEXT,
                    updated_at TEXT,
                    FOREIGN KEY (document_id) REFERENCES reader_documents(id) ON DELETE CASCADE
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS reader_suggested_questions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    document_id INTEGER NOT NULL,
                    page_num INTEGER NOT NULL,
                    questions TEXT NOT NULL DEFAULT '[]',
                    created_at TEXT,
                    FOREIGN KEY (document_id) REFERENCES reader_documents(id) ON DELETE CASCADE,
                    UNIQUE(document_id, page_num)
                )
            """)

            # Migrate: add session_id column to reader_chats if missing
            cols = [row["name"] for row in conn.execute("PRAGMA table_info(reader_chats)").fetchall()]
            if "session_id" not in cols:
                conn.execute("ALTER TABLE reader_chats ADD COLUMN session_id INTEGER DEFAULT NULL")
                # Bind orphan chats to a default session per document
                orphan_docs = conn.execute(
                    "SELECT DISTINCT document_id FROM reader_chats WHERE session_id IS NULL"
                ).fetchall()
                for row in orphan_docs:
                    doc_id = row["document_id"]
                    now = self._beijing_now()
                    cursor = conn.execute(
                        "INSERT INTO reader_sessions (document_id, title, created_at, updated_at) VALUES (?, ?, ?, ?)",
                        (doc_id, "默认对话", now, now),
                    )
                    session_id = cursor.lastrowid
                    conn.execute(
                        "UPDATE reader_chats SET session_id = ? WHERE document_id = ? AND session_id IS NULL",
                        (session_id, doc_id),
                    )
                logger.debug("Migrated orphan chats to default sessions")

            conn.commit()
        logger.debug("Reader tables initialized")

    # --- Document CRUD ---

    def create_document(
        self,
        title: str,
        file_name: str,
        file_type: str,
        file_path: str,
        total_pages: int = 0,
    ) -> dict:
        now = self._beijing_now()
        with self._connect() as conn:
            cursor = conn.execute(
                """INSERT INTO reader_documents
                   (title, file_name, file_type, file_path, total_pages, current_page, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, 1, ?, ?)""",
                (title, file_name, file_type, file_path, total_pages, now, now),
            )
            conn.commit()
            doc_id = cursor.lastrowid
        logger.info(f"Reader document created: {title} (id={doc_id})")
        return self.get_document(doc_id)  # type: ignore

    def list_documents(self) -> list[dict]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM reader_documents ORDER BY updated_at DESC"
            ).fetchall()
        return [dict(r) for r in rows]

    def get_document(self, doc_id: int) -> dict | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM reader_documents WHERE id = ?", (doc_id,)
            ).fetchone()
        return dict(row) if row else None

    def delete_document(self, doc_id: int) -> bool:
        with self._connect() as conn:
            # CASCADE will handle pages and chats
            cursor = conn.execute(
                "DELETE FROM reader_documents WHERE id = ?", (doc_id,)
            )
            conn.commit()
        deleted = cursor.rowcount > 0
        if deleted:
            logger.info(f"Reader document deleted: id={doc_id}")
        return deleted

    def update_progress(self, doc_id: int, current_page: int) -> dict | None:
        now = self._beijing_now()
        with self._connect() as conn:
            conn.execute(
                "UPDATE reader_documents SET current_page = ?, updated_at = ? WHERE id = ?",
                (current_page, now, doc_id),
            )
            conn.commit()
        return self.get_document(doc_id)

    # --- Page CRUD ---

    def insert_pages(self, doc_id: int, pages: list[str]) -> None:
        """Bulk insert pages for a document."""
        with self._connect() as conn:
            conn.executemany(
                "INSERT INTO reader_pages (document_id, page_num, content) VALUES (?, ?, ?)",
                [(doc_id, i + 1, content) for i, content in enumerate(pages)],
            )
            conn.commit()
        logger.debug(f"Inserted {len(pages)} pages for doc_id={doc_id}")

    def get_page_content(self, doc_id: int, page_num: int) -> str | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT content FROM reader_pages WHERE document_id = ? AND page_num = ?",
                (doc_id, page_num),
            ).fetchone()
        return row["content"] if row else None

    def get_page_range(self, doc_id: int, start: int, end: int) -> list[dict]:
        """Get pages in range [start, end] inclusive."""
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT page_num, content FROM reader_pages WHERE document_id = ? AND page_num >= ? AND page_num <= ? ORDER BY page_num",
                (doc_id, start, end),
            ).fetchall()
        return [dict(r) for r in rows]

    # --- Session CRUD ---

    def create_session(self, doc_id: int, title: str = "新对话") -> dict:
        now = self._beijing_now()
        with self._connect() as conn:
            cursor = conn.execute(
                "INSERT INTO reader_sessions (document_id, title, created_at, updated_at) VALUES (?, ?, ?, ?)",
                (doc_id, title, now, now),
            )
            conn.commit()
            session_id = cursor.lastrowid
        logger.info(f"Reader session created: id={session_id}, doc_id={doc_id}")
        return self.get_session(session_id)  # type: ignore

    def list_sessions(self, doc_id: int) -> list[dict]:
        with self._connect() as conn:
            rows = conn.execute(
                """SELECT s.*, COUNT(c.id) AS message_count
                   FROM reader_sessions s
                   LEFT JOIN reader_chats c ON c.session_id = s.id
                   WHERE s.document_id = ?
                   GROUP BY s.id
                   ORDER BY s.updated_at DESC""",
                (doc_id,),
            ).fetchall()
        return [dict(r) for r in rows]

    def get_session(self, session_id: int) -> dict | None:
        with self._connect() as conn:
            row = conn.execute(
                """SELECT s.*, COUNT(c.id) AS message_count
                   FROM reader_sessions s
                   LEFT JOIN reader_chats c ON c.session_id = s.id
                   WHERE s.id = ?
                   GROUP BY s.id""",
                (session_id,),
            ).fetchone()
        return dict(row) if row else None

    def delete_session(self, session_id: int) -> bool:
        with self._connect() as conn:
            conn.execute("DELETE FROM reader_chats WHERE session_id = ?", (session_id,))
            cursor = conn.execute("DELETE FROM reader_sessions WHERE id = ?", (session_id,))
            conn.commit()
        deleted = cursor.rowcount > 0
        if deleted:
            logger.info(f"Reader session deleted: id={session_id}")
        return deleted

    def update_session_title(self, session_id: int, title: str) -> None:
        now = self._beijing_now()
        with self._connect() as conn:
            conn.execute(
                "UPDATE reader_sessions SET title = ?, updated_at = ? WHERE id = ?",
                (title, now, session_id),
            )
            conn.commit()

    def touch_session(self, session_id: int) -> None:
        now = self._beijing_now()
        with self._connect() as conn:
            conn.execute(
                "UPDATE reader_sessions SET updated_at = ? WHERE id = ?",
                (now, session_id),
            )
            conn.commit()

    # --- Chat CRUD ---

    def add_chat(
        self, doc_id: int, role: str, content: str, page_num: int = 1,
        session_id: int | None = None,
    ) -> dict:
        now = self._beijing_now()
        with self._connect() as conn:
            cursor = conn.execute(
                "INSERT INTO reader_chats (document_id, role, content, page_num, session_id, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (doc_id, role, content, page_num, session_id, now),
            )
            conn.commit()
            chat_id = cursor.lastrowid
            row = conn.execute(
                "SELECT * FROM reader_chats WHERE id = ?", (chat_id,)
            ).fetchone()
        return dict(row)

    def get_chat_history(
        self, doc_id: int, limit: int = 50, session_id: int | None = None,
    ) -> list[dict]:
        with self._connect() as conn:
            if session_id is not None:
                rows = conn.execute(
                    "SELECT * FROM reader_chats WHERE document_id = ? AND session_id = ? ORDER BY id ASC LIMIT ?",
                    (doc_id, session_id, limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM reader_chats WHERE document_id = ? ORDER BY id ASC LIMIT ?",
                    (doc_id, limit),
                ).fetchall()
        return [dict(r) for r in rows]

    def clear_chat(self, doc_id: int, session_id: int | None = None) -> None:
        with self._connect() as conn:
            if session_id is not None:
                conn.execute(
                    "DELETE FROM reader_chats WHERE document_id = ? AND session_id = ?",
                    (doc_id, session_id),
                )
            else:
                conn.execute(
                    "DELETE FROM reader_chats WHERE document_id = ?", (doc_id,)
                )
            conn.commit()
        logger.info(f"Chat history cleared for doc_id={doc_id}, session_id={session_id}")

    # --- Suggested Questions ---

    def get_suggestions(self, doc_id: int, page_num: int) -> list[str] | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT questions FROM reader_suggested_questions WHERE document_id = ? AND page_num = ?",
                (doc_id, page_num),
            ).fetchone()
        if row is None:
            return None
        return json.loads(row["questions"])

    def save_suggestions(self, doc_id: int, page_num: int, questions: list[str]) -> None:
        now = self._beijing_now()
        with self._connect() as conn:
            conn.execute(
                """INSERT INTO reader_suggested_questions (document_id, page_num, questions, created_at)
                   VALUES (?, ?, ?, ?)
                   ON CONFLICT(document_id, page_num) DO UPDATE SET questions = excluded.questions, created_at = excluded.created_at""",
                (doc_id, page_num, json.dumps(questions, ensure_ascii=False), now),
            )
            conn.commit()
