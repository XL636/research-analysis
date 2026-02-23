"""论文项目 SQLite 持久化."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

import yaml
from loguru import logger

from src.core.paper_models import PaperProject


class PaperStore:
    """论文项目持久化存储，复用知识库同一 DB."""

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
        """返回北京时间字符串."""
        return datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m-%d %H:%M:%S")

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        """初始化 paper_projects 表."""
        with self._connect() as conn:
            # 确保 _meta 表存在
            conn.execute(
                "CREATE TABLE IF NOT EXISTS _meta (key TEXT PRIMARY KEY, value TEXT)"
            )

            migrated = conn.execute(
                "SELECT value FROM _meta WHERE key = 'paper_projects_created'"
            ).fetchone()
            if not migrated:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS paper_projects (
                        id TEXT PRIMARY KEY,
                        name TEXT NOT NULL,
                        status TEXT NOT NULL,
                        project_json TEXT NOT NULL,
                        created_at TEXT,
                        updated_at TEXT
                    )
                """)
                conn.execute(
                    "INSERT OR REPLACE INTO _meta (key, value) VALUES ('paper_projects_created', '1')"
                )
                conn.commit()
                logger.info("paper_projects table created")

    def save(self, project: PaperProject) -> None:
        """保存或更新论文项目."""
        now = self._beijing_now()
        if not project.created_at:
            project.created_at = now
        project.updated_at = now

        project_json = project.model_dump_json()

        with self._connect() as conn:
            conn.execute(
                """INSERT OR REPLACE INTO paper_projects (id, name, status, project_json, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (project.id, project.name, project.status.value, project_json, project.created_at, project.updated_at),
            )
            conn.commit()

        logger.info(f"Saved paper project: {project.name} (id={project.id}, status={project.status.value})")

    def load(self, project_id: str) -> PaperProject | None:
        """加载论文项目."""
        with self._connect() as conn:
            row = conn.execute(
                "SELECT project_json FROM paper_projects WHERE id = ?", (project_id,)
            ).fetchone()

        if row and row["project_json"]:
            return PaperProject.model_validate_json(row["project_json"])
        return None

    def list_projects(self, limit: int = 50) -> list[dict]:
        """列出论文项目摘要."""
        with self._connect() as conn:
            rows = conn.execute(
                """SELECT id, name, status, created_at, updated_at
                   FROM paper_projects
                   ORDER BY updated_at DESC
                   LIMIT ?""",
                (limit,),
            ).fetchall()

        return [
            {
                "id": row["id"],
                "name": row["name"],
                "status": row["status"],
                "created_at": row["created_at"] or "",
                "updated_at": row["updated_at"] or "",
            }
            for row in rows
        ]

    def delete(self, project_id: str) -> bool:
        """删除论文项目."""
        with self._connect() as conn:
            row = conn.execute(
                "SELECT id FROM paper_projects WHERE id = ?", (project_id,)
            ).fetchone()
            if not row:
                return False
            conn.execute("DELETE FROM paper_projects WHERE id = ?", (project_id,))
            conn.commit()

        logger.info(f"Deleted paper project: {project_id}")
        return True
