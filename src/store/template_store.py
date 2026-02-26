"""报告模板存储 - SQLite CRUD + 内置模板同步."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

import yaml
from loguru import logger

from src.core.models import ReportTemplate, TemplateSection


# 内置模板定义：name -> (display_name, description, prompt_file)
BUILTIN_TEMPLATES: dict[str, tuple[str, str, str]] = {
    "default": ("标准报告", "通用学术分析报告模板", "config/prompts/generator_system.txt"),
    "meeting": ("会议报告", "组会/研讨会报告模板", "config/prompts/meeting_report.txt"),
    "quick": ("快速摘要", "简洁快速的文档摘要", "config/prompts/generator_quick.txt"),
    "deep": ("深度研究", "深入详细的研究分析报告", "config/prompts/generator_deep.txt"),
}


class TemplateStore:
    """报告模板存储：SQLite 持久化 + 内置模板管理."""

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
                CREATE TABLE IF NOT EXISTS report_templates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    display_name TEXT NOT NULL,
                    description TEXT DEFAULT '',
                    prompt_content TEXT NOT NULL,
                    sections_json TEXT DEFAULT '[]',
                    is_builtin INTEGER DEFAULT 0,
                    created_at TEXT,
                    updated_at TEXT
                )
            """)
            # Ensure _meta table exists (shared with knowledge_base)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS _meta (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            """)
            conn.commit()

        self._sync_builtin_templates()

    def _sync_builtin_templates(self) -> None:
        """同步内置模板：新增缺失的，更新已有的 prompt_content."""
        with self._connect() as conn:
            for name, (display_name, description, prompt_file) in BUILTIN_TEMPLATES.items():
                prompt_path = Path(prompt_file)
                if not prompt_path.exists():
                    logger.warning(f"Builtin template prompt file not found: {prompt_file}")
                    continue

                prompt_content = prompt_path.read_text(encoding="utf-8")
                now = self._beijing_now()

                existing = conn.execute(
                    "SELECT id FROM report_templates WHERE name = ?", (name,)
                ).fetchone()

                if existing:
                    # 更新内置模板的 prompt_content（保持同步）
                    conn.execute(
                        """UPDATE report_templates
                           SET prompt_content = ?, display_name = ?, description = ?, updated_at = ?
                           WHERE name = ? AND is_builtin = 1""",
                        (prompt_content, display_name, description, now, name),
                    )
                else:
                    conn.execute(
                        """INSERT INTO report_templates
                           (name, display_name, description, prompt_content, sections_json, is_builtin, created_at, updated_at)
                           VALUES (?, ?, ?, ?, '[]', 1, ?, ?)""",
                        (name, display_name, description, prompt_content, now, now),
                    )

            conn.commit()
        logger.debug("Builtin templates synced")

    def _row_to_template(self, row: sqlite3.Row) -> ReportTemplate:
        sections = []
        try:
            raw_sections = json.loads(row["sections_json"] or "[]")
            sections = [TemplateSection(**s) for s in raw_sections]
        except (json.JSONDecodeError, TypeError):
            pass

        return ReportTemplate(
            id=row["id"],
            name=row["name"],
            display_name=row["display_name"],
            description=row["description"] or "",
            prompt_content=row["prompt_content"],
            sections=sections,
            is_builtin=bool(row["is_builtin"]),
            created_at=row["created_at"] or "",
            updated_at=row["updated_at"] or "",
        )

    def list_templates(self) -> list[ReportTemplate]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM report_templates ORDER BY is_builtin DESC, id ASC"
            ).fetchall()
        return [self._row_to_template(r) for r in rows]

    def get_template(self, template_id: int) -> ReportTemplate | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM report_templates WHERE id = ?", (template_id,)
            ).fetchone()
        return self._row_to_template(row) if row else None

    def get_template_by_name(self, name: str) -> ReportTemplate | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM report_templates WHERE name = ?", (name,)
            ).fetchone()
        return self._row_to_template(row) if row else None

    def create_template(
        self,
        name: str,
        display_name: str,
        description: str = "",
        prompt_content: str = "",
        sections: list[TemplateSection] | None = None,
    ) -> ReportTemplate:
        now = self._beijing_now()
        sections_json = json.dumps(
            [s.model_dump() for s in (sections or [])], ensure_ascii=False
        )

        with self._connect() as conn:
            cursor = conn.execute(
                """INSERT INTO report_templates
                   (name, display_name, description, prompt_content, sections_json, is_builtin, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, 0, ?, ?)""",
                (name, display_name, description, prompt_content, sections_json, now, now),
            )
            conn.commit()
            template_id = cursor.lastrowid

        logger.info(f"Created template: {name} (id={template_id})")
        return self.get_template(template_id)  # type: ignore

    def update_template(
        self,
        template_id: int,
        display_name: str | None = None,
        description: str | None = None,
        prompt_content: str | None = None,
        sections: list[TemplateSection] | None = None,
    ) -> ReportTemplate | None:
        template = self.get_template(template_id)
        if not template:
            return None

        # 内置模板不允许修改 prompt_content
        if template.is_builtin and prompt_content is not None:
            raise ValueError("Cannot modify prompt_content of builtin templates")

        now = self._beijing_now()
        updates = []
        params = []

        if display_name is not None and not template.is_builtin:
            updates.append("display_name = ?")
            params.append(display_name)
        if description is not None:
            updates.append("description = ?")
            params.append(description)
        if prompt_content is not None and not template.is_builtin:
            updates.append("prompt_content = ?")
            params.append(prompt_content)
        if sections is not None and not template.is_builtin:
            updates.append("sections_json = ?")
            params.append(json.dumps([s.model_dump() for s in sections], ensure_ascii=False))

        if not updates:
            return template

        updates.append("updated_at = ?")
        params.append(now)
        params.append(template_id)

        with self._connect() as conn:
            conn.execute(
                f"UPDATE report_templates SET {', '.join(updates)} WHERE id = ?",
                params,
            )
            conn.commit()

        logger.info(f"Updated template id={template_id}")
        return self.get_template(template_id)

    def delete_template(self, template_id: int) -> bool:
        template = self.get_template(template_id)
        if not template:
            return False
        if template.is_builtin:
            raise ValueError("Cannot delete builtin templates")

        with self._connect() as conn:
            conn.execute("DELETE FROM report_templates WHERE id = ?", (template_id,))
            conn.commit()

        logger.info(f"Deleted template id={template_id}")
        return True
