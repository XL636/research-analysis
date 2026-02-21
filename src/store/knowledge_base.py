"""SQLite + FTS5 知识库 - 存储分析结果，支持全文搜索."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import yaml
from loguru import logger

from src.core.models import AnalysisResult


class KnowledgeBase:
    """知识库：SQLite + FTS5 全文搜索."""

    def __init__(self, db_path: str | None = None):
        if db_path is None:
            # 从配置读取
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

    def _init_db(self) -> None:
        """初始化数据库表结构."""
        with self._connect() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS documents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    file_path TEXT,
                    file_type TEXT,
                    summary TEXT,
                    content TEXT,
                    analysis_json TEXT,
                    created_at TEXT DEFAULT (datetime('now')),
                    updated_at TEXT DEFAULT (datetime('now'))
                );

                CREATE TABLE IF NOT EXISTS tags (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL
                );

                CREATE TABLE IF NOT EXISTS document_tags (
                    document_id INTEGER REFERENCES documents(id),
                    tag_id INTEGER REFERENCES tags(id),
                    PRIMARY KEY (document_id, tag_id)
                );

                CREATE VIRTUAL TABLE IF NOT EXISTS documents_fts USING fts5(
                    title, summary, content
                );
            """)

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def store_analysis(self, analysis: AnalysisResult, file_path: str = "", file_type: str = "") -> int:
        """存储分析结果到知识库.

        Returns:
            文档 ID
        """
        content = analysis.summary
        if analysis.key_findings:
            content += "\n" + "\n".join(kf.finding for kf in analysis.key_findings)
        if analysis.contributions:
            content += "\n" + "\n".join(analysis.contributions)

        analysis_json = analysis.model_dump_json()

        with self._connect() as conn:
            cursor = conn.execute(
                """INSERT INTO documents (title, file_path, file_type, summary, content, analysis_json)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (analysis.document_title, file_path, file_type, analysis.summary, content, analysis_json),
            )
            doc_id = cursor.lastrowid

            # 同步 FTS 索引
            conn.execute(
                "INSERT INTO documents_fts (rowid, title, summary, content) VALUES (?, ?, ?, ?)",
                (doc_id, analysis.document_title, analysis.summary, content),
            )

            # 添加标签
            for tag_name in analysis.tags:
                conn.execute("INSERT OR IGNORE INTO tags (name) VALUES (?)", (tag_name,))
                tag_row = conn.execute("SELECT id FROM tags WHERE name = ?", (tag_name,)).fetchone()
                if tag_row:
                    conn.execute(
                        "INSERT OR IGNORE INTO document_tags (document_id, tag_id) VALUES (?, ?)",
                        (doc_id, tag_row["id"]),
                    )

            conn.commit()

        logger.info(f"Stored analysis: {analysis.document_title} (id={doc_id})")
        return doc_id

    def search(self, query: str, limit: int = 10) -> list[dict]:
        """全文搜索知识库.

        Args:
            query: 搜索关键词
            limit: 最大结果数

        Returns:
            搜索结果列表
        """
        with self._connect() as conn:
            rows = conn.execute(
                """SELECT d.id, d.title, d.file_type, d.summary, d.created_at,
                          GROUP_CONCAT(t.name, ', ') as tags
                   FROM documents_fts fts
                   JOIN documents d ON d.id = fts.rowid
                   LEFT JOIN document_tags dt ON dt.document_id = d.id
                   LEFT JOIN tags t ON t.id = dt.tag_id
                   WHERE documents_fts MATCH ?
                   GROUP BY d.id
                   ORDER BY fts.rank
                   LIMIT ?""",
                (query, limit),
            ).fetchall()

        return [
            {
                "id": row["id"],
                "title": row["title"],
                "file_type": row["file_type"] or "",
                "summary": row["summary"] or "",
                "tags": row["tags"] or "",
                "date": row["created_at"] or "",
            }
            for row in rows
        ]

    def list_documents(self, tag: str | None = None, limit: int = 20) -> list[dict]:
        """列出知识库中的文档.

        Args:
            tag: 按标签筛选（可选）
            limit: 最大结果数

        Returns:
            文档列表
        """
        with self._connect() as conn:
            if tag:
                rows = conn.execute(
                    """SELECT d.id, d.title, d.file_type, d.created_at,
                              GROUP_CONCAT(t.name, ', ') as tags
                       FROM documents d
                       JOIN document_tags dt ON dt.document_id = d.id
                       JOIN tags t ON t.id = dt.tag_id
                       WHERE t.name = ?
                       GROUP BY d.id
                       ORDER BY d.created_at DESC
                       LIMIT ?""",
                    (tag, limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    """SELECT d.id, d.title, d.file_type, d.created_at,
                              GROUP_CONCAT(t.name, ', ') as tags
                       FROM documents d
                       LEFT JOIN document_tags dt ON dt.document_id = d.id
                       LEFT JOIN tags t ON t.id = dt.tag_id
                       GROUP BY d.id
                       ORDER BY d.created_at DESC
                       LIMIT ?""",
                    (limit,),
                ).fetchall()

        return [
            {
                "id": row["id"],
                "title": row["title"],
                "file_type": row["file_type"] or "",
                "tags": row["tags"] or "",
                "date": row["created_at"] or "",
            }
            for row in rows
        ]

    def get_analysis(self, doc_id: int) -> AnalysisResult | None:
        """获取存储的分析结果."""
        with self._connect() as conn:
            row = conn.execute(
                "SELECT analysis_json FROM documents WHERE id = ?", (doc_id,)
            ).fetchone()

        if row and row["analysis_json"]:
            return AnalysisResult.model_validate_json(row["analysis_json"])
        return None
