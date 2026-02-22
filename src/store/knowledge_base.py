"""SQLite + FTS5 知识库 - 存储分析结果，支持全文搜索."""

from __future__ import annotations

import csv
import io
import json
import sqlite3
from datetime import datetime, timezone, timedelta
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

    @staticmethod
    def _beijing_now() -> str:
        """返回北京时间字符串."""
        return datetime.now(timezone(timedelta(hours=8))).strftime('%Y-%m-%d %H:%M:%S')

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
                    created_at TEXT DEFAULT (datetime('now', '+8 hours')),
                    updated_at TEXT DEFAULT (datetime('now', '+8 hours'))
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

                CREATE TABLE IF NOT EXISTS _meta (
                    key TEXT PRIMARY KEY,
                    value TEXT
                );
            """)

            # 一次性时区迁移：旧数据库中 datetime('now') 生成的 UTC 时间 → +8h
            migrated = conn.execute(
                "SELECT value FROM _meta WHERE key = 'tz_migrated'"
            ).fetchone()
            if not migrated:
                conn.execute(
                    """UPDATE documents SET
                           created_at = datetime(created_at, '+8 hours'),
                           updated_at = datetime(updated_at, '+8 hours')
                       WHERE created_at IS NOT NULL AND length(created_at) > 0"""
                )
                conn.execute(
                    "INSERT OR REPLACE INTO _meta (key, value) VALUES ('tz_migrated', '1')"
                )
                conn.commit()
                logger.info("Timezone migration completed: UTC → Beijing time")

            # Collections 迁移
            collections_migrated = conn.execute(
                "SELECT value FROM _meta WHERE key = 'collections_migrated'"
            ).fetchone()
            if not collections_migrated:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS collections (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        created_at TEXT
                    )
                """)
                # 检查 documents 表是否已有 collection_id 列
                cols = [r[1] for r in conn.execute("PRAGMA table_info(documents)").fetchall()]
                if "collection_id" not in cols:
                    conn.execute("ALTER TABLE documents ADD COLUMN collection_id INTEGER REFERENCES collections(id)")
                conn.execute(
                    "INSERT OR REPLACE INTO _meta (key, value) VALUES ('collections_migrated', '1')"
                )
                conn.commit()
                logger.info("Collections migration completed")

            # report_content 迁移
            report_migrated = conn.execute(
                "SELECT value FROM _meta WHERE key = 'report_content_migrated'"
            ).fetchone()
            if not report_migrated:
                cols = [r[1] for r in conn.execute("PRAGMA table_info(documents)").fetchall()]
                if "report_content" not in cols:
                    conn.execute("ALTER TABLE documents ADD COLUMN report_content TEXT")
                conn.execute(
                    "INSERT OR REPLACE INTO _meta (key, value) VALUES ('report_content_migrated', '1')"
                )
                conn.commit()
                logger.info("report_content migration completed")

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

        beijing_now = self._beijing_now()

        with self._connect() as conn:
            cursor = conn.execute(
                """INSERT INTO documents (title, file_path, file_type, summary, content, analysis_json, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (analysis.document_title, file_path, file_type, analysis.summary, content, analysis_json, beijing_now, beijing_now),
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
                """SELECT d.id, d.title, d.file_type, d.summary,
                          strftime('%Y-%m-%d %H:%M', d.created_at) as created_at,
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

    def list_documents(
        self,
        tag: str | None = None,
        limit: int = 20,
        collection_id: int | None = None,
        uncategorized: bool = False,
    ) -> list[dict]:
        """列出知识库中的文档.

        Args:
            tag: 按标签筛选（可选）
            limit: 最大结果数
            collection_id: 按分组筛选（可选）
            uncategorized: 只显示未分类文档

        Returns:
            文档列表
        """
        with self._connect() as conn:
            where_clauses: list[str] = []
            params: list = []

            if tag:
                where_clauses.append("t.name = ?")
                params.append(tag)

            if collection_id is not None:
                where_clauses.append("d.collection_id = ?")
                params.append(collection_id)
            elif uncategorized:
                where_clauses.append("d.collection_id IS NULL")

            base_select = """SELECT d.id, d.title, d.file_type, d.collection_id,
                              strftime('%Y-%m-%d %H:%M', d.created_at) as created_at,
                              GROUP_CONCAT(t.name, ', ') as tags
                       FROM documents d
                       LEFT JOIN document_tags dt ON dt.document_id = d.id
                       LEFT JOIN tags t ON t.id = dt.tag_id"""

            if tag:
                # 用 JOIN 而非 LEFT JOIN 来筛选标签
                base_select = """SELECT d.id, d.title, d.file_type, d.collection_id,
                              strftime('%Y-%m-%d %H:%M', d.created_at) as created_at,
                              GROUP_CONCAT(t.name, ', ') as tags
                       FROM documents d
                       JOIN document_tags dt ON dt.document_id = d.id
                       JOIN tags t ON t.id = dt.tag_id"""

            where_sql = ""
            if where_clauses:
                where_sql = " WHERE " + " AND ".join(where_clauses)

            query = f"{base_select}{where_sql} GROUP BY d.id ORDER BY d.created_at DESC LIMIT ?"
            params.append(limit)

            rows = conn.execute(query, params).fetchall()

        return [
            {
                "id": row["id"],
                "title": row["title"],
                "file_type": row["file_type"] or "",
                "tags": row["tags"] or "",
                "date": row["created_at"] or "",
                "collection_id": row["collection_id"],
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

    def export_json(self, path: str) -> int:
        """导出全部文档+分析为 JSON 文件.

        Returns:
            导出的文档数量
        """
        with self._connect() as conn:
            rows = conn.execute(
                """SELECT d.id, d.title, d.file_path, d.file_type, d.summary,
                          d.content, d.analysis_json, d.report_content,
                          d.created_at, d.updated_at,
                          GROUP_CONCAT(t.name, ', ') as tags
                   FROM documents d
                   LEFT JOIN document_tags dt ON dt.document_id = d.id
                   LEFT JOIN tags t ON t.id = dt.tag_id
                   GROUP BY d.id
                   ORDER BY d.id"""
            ).fetchall()

        documents = []
        for row in rows:
            doc = {
                "id": row["id"],
                "title": row["title"],
                "file_path": row["file_path"] or "",
                "file_type": row["file_type"] or "",
                "summary": row["summary"] or "",
                "content": row["content"] or "",
                "analysis_json": row["analysis_json"] or "",
                "report_content": row["report_content"] or "",
                "created_at": row["created_at"] or "",
                "updated_at": row["updated_at"] or "",
                "tags": [t.strip() for t in (row["tags"] or "").split(",") if t.strip()],
            }
            documents.append(doc)

        export_data = {
            "version": "1.0",
            "document_count": len(documents),
            "documents": documents,
        }

        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)

        logger.info(f"Exported {len(documents)} documents to {path}")
        return len(documents)

    def export_csv(self, path: str) -> int:
        """导出摘要表格为 CSV.

        Returns:
            导出的文档数量
        """
        with self._connect() as conn:
            rows = conn.execute(
                """SELECT d.id, d.title, d.file_path, d.file_type, d.summary,
                          d.created_at, GROUP_CONCAT(t.name, ', ') as tags
                   FROM documents d
                   LEFT JOIN document_tags dt ON dt.document_id = d.id
                   LEFT JOIN tags t ON t.id = dt.tag_id
                   GROUP BY d.id
                   ORDER BY d.id"""
            ).fetchall()

        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["id", "title", "file_path", "file_type", "summary", "tags", "created_at"])
            for row in rows:
                writer.writerow([
                    row["id"],
                    row["title"],
                    row["file_path"] or "",
                    row["file_type"] or "",
                    row["summary"] or "",
                    row["tags"] or "",
                    row["created_at"] or "",
                ])

        count = len(rows)
        logger.info(f"Exported {count} documents to {path}")
        return count

    def import_json(self, path: str) -> int:
        """从 JSON 文件导入文档到知识库.

        Returns:
            导入的文档数量
        """
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        documents = data.get("documents", [])
        imported = 0

        with self._connect() as conn:
            for doc in documents:
                # 插入文档
                cursor = conn.execute(
                    """INSERT INTO documents (title, file_path, file_type, summary, content, analysis_json, report_content, created_at, updated_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        doc["title"],
                        doc.get("file_path", ""),
                        doc.get("file_type", ""),
                        doc.get("summary", ""),
                        doc.get("content", ""),
                        doc.get("analysis_json", ""),
                        doc.get("report_content", ""),
                        doc.get("created_at", ""),
                        doc.get("updated_at", ""),
                    ),
                )
                doc_id = cursor.lastrowid

                # 同步 FTS 索引
                conn.execute(
                    "INSERT INTO documents_fts (rowid, title, summary, content) VALUES (?, ?, ?, ?)",
                    (doc_id, doc["title"], doc.get("summary", ""), doc.get("content", "")),
                )

                # 添加标签
                for tag_name in doc.get("tags", []):
                    if tag_name:
                        conn.execute("INSERT OR IGNORE INTO tags (name) VALUES (?)", (tag_name,))
                        tag_row = conn.execute("SELECT id FROM tags WHERE name = ?", (tag_name,)).fetchone()
                        if tag_row:
                            conn.execute(
                                "INSERT OR IGNORE INTO document_tags (document_id, tag_id) VALUES (?, ?)",
                                (doc_id, tag_row["id"]),
                            )

                imported += 1

            conn.commit()

        logger.info(f"Imported {imported} documents from {path}")
        return imported

    def update_report_content(self, doc_id: int, report_content: str) -> bool:
        """存储完整报告内容到文档.

        Returns:
            是否成功更新
        """
        beijing_now = self._beijing_now()
        with self._connect() as conn:
            row = conn.execute("SELECT id FROM documents WHERE id = ?", (doc_id,)).fetchone()
            if not row:
                return False
            conn.execute(
                "UPDATE documents SET report_content = ?, updated_at = ? WHERE id = ?",
                (report_content, beijing_now, doc_id),
            )
            conn.commit()
        logger.info(f"Stored report_content for doc id={doc_id}")
        return True

    def get_report_content(self, doc_id: int) -> str | None:
        """获取文档的完整报告内容."""
        with self._connect() as conn:
            row = conn.execute(
                "SELECT report_content FROM documents WHERE id = ?", (doc_id,)
            ).fetchone()
        if row and row["report_content"]:
            return row["report_content"]
        return None

    def delete_document(self, doc_id: int) -> bool:
        """删除文档及其关联数据（FTS、标签）.

        Returns:
            是否成功删除
        """
        with self._connect() as conn:
            row = conn.execute("SELECT id FROM documents WHERE id = ?", (doc_id,)).fetchone()
            if not row:
                return False

            conn.execute("DELETE FROM documents_fts WHERE rowid = ?", (doc_id,))
            conn.execute("DELETE FROM document_tags WHERE document_id = ?", (doc_id,))
            conn.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
            conn.commit()

        logger.info(f"Deleted document id={doc_id}")
        return True

    def update_title(self, doc_id: int, new_title: str) -> bool:
        """更新文档标题（含 FTS 索引重建）.

        Returns:
            是否成功更新
        """
        beijing_now = self._beijing_now()
        with self._connect() as conn:
            row = conn.execute(
                "SELECT id, summary, content FROM documents WHERE id = ?", (doc_id,)
            ).fetchone()
            if not row:
                return False

            conn.execute(
                "UPDATE documents SET title = ?, updated_at = ? WHERE id = ?",
                (new_title, beijing_now, doc_id),
            )
            # FTS5 不支持 UPDATE，需要 DELETE + INSERT 重建索引
            conn.execute("DELETE FROM documents_fts WHERE rowid = ?", (doc_id,))
            conn.execute(
                "INSERT INTO documents_fts (rowid, title, summary, content) VALUES (?, ?, ?, ?)",
                (doc_id, new_title, row["summary"] or "", row["content"] or ""),
            )
            conn.commit()

        logger.info(f"Updated title for doc id={doc_id}: {new_title}")
        return True

    # ── Collections ──

    def create_collection(self, name: str) -> int:
        """创建分组.

        Returns:
            新分组 ID
        """
        beijing_now = self._beijing_now()
        with self._connect() as conn:
            cursor = conn.execute(
                "INSERT INTO collections (name, created_at) VALUES (?, ?)",
                (name, beijing_now),
            )
            conn.commit()
            return cursor.lastrowid

    def list_collections(self) -> list[dict]:
        """列出分组 + 文档计数."""
        with self._connect() as conn:
            rows = conn.execute(
                """SELECT c.id, c.name,
                          COUNT(d.id) as document_count
                   FROM collections c
                   LEFT JOIN documents d ON d.collection_id = c.id
                   GROUP BY c.id
                   ORDER BY c.name"""
            ).fetchall()

        return [
            {
                "id": row["id"],
                "name": row["name"],
                "document_count": row["document_count"],
            }
            for row in rows
        ]

    def rename_collection(self, collection_id: int, name: str) -> bool:
        """重命名分组."""
        with self._connect() as conn:
            row = conn.execute(
                "SELECT id FROM collections WHERE id = ?", (collection_id,)
            ).fetchone()
            if not row:
                return False
            conn.execute(
                "UPDATE collections SET name = ? WHERE id = ?",
                (name, collection_id),
            )
            conn.commit()
        return True

    def delete_collection(self, collection_id: int) -> bool:
        """删除分组（文档归入未分类）."""
        with self._connect() as conn:
            row = conn.execute(
                "SELECT id FROM collections WHERE id = ?", (collection_id,)
            ).fetchone()
            if not row:
                return False
            conn.execute(
                "UPDATE documents SET collection_id = NULL WHERE collection_id = ?",
                (collection_id,),
            )
            conn.execute("DELETE FROM collections WHERE id = ?", (collection_id,))
            conn.commit()
        logger.info(f"Deleted collection id={collection_id}")
        return True

    def move_document_to_collection(self, doc_id: int, collection_id: int | None) -> bool:
        """移动文档到分组（collection_id=None 表示移到未分类）."""
        with self._connect() as conn:
            row = conn.execute(
                "SELECT id FROM documents WHERE id = ?", (doc_id,)
            ).fetchone()
            if not row:
                return False
            if collection_id is not None:
                coll = conn.execute(
                    "SELECT id FROM collections WHERE id = ?", (collection_id,)
                ).fetchone()
                if not coll:
                    return False
            conn.execute(
                "UPDATE documents SET collection_id = ? WHERE id = ?",
                (collection_id, doc_id),
            )
            conn.commit()
        return True

    def find_by_filename(self, filename: str) -> list[dict]:
        """按文件名查找文档（用于重复检测）.

        Args:
            filename: 文件名（不含路径）

        Returns:
            匹配的文档列表
        """
        with self._connect() as conn:
            rows = conn.execute(
                """SELECT d.id, d.title, d.file_type,
                          strftime('%Y-%m-%d %H:%M', d.created_at) as created_at,
                          GROUP_CONCAT(t.name, ', ') as tags
                   FROM documents d
                   LEFT JOIN document_tags dt ON dt.document_id = d.id
                   LEFT JOIN tags t ON t.id = dt.tag_id
                   WHERE d.file_path LIKE ?
                   GROUP BY d.id
                   ORDER BY d.created_at DESC""",
                (f"%{filename}",),
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
