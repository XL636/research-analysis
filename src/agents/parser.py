"""解析 Agent - 调度解析器，对提取文本做初步结构化."""

from __future__ import annotations

from pathlib import Path

from loguru import logger

from src.agents.base import BaseAgent
from src.core.models import FileType, ParsedDocument
from src.parsers.pdf_parser import parse_pdf


class ParserAgent(BaseAgent):
    """解析 Agent：根据文件类型选择解析器，返回 ParsedDocument."""

    agent_type = "parser"

    def _detect_file_type(self, file_path: str) -> FileType:
        suffix = Path(file_path).suffix.lower()
        type_map = {
            ".pdf": FileType.PDF,
            ".pptx": FileType.PPTX,
            ".ppt": FileType.PPTX,
            ".md": FileType.MARKDOWN,
            ".markdown": FileType.MARKDOWN,
            ".txt": FileType.TXT,
            ".docx": FileType.DOCX,
            ".doc": FileType.DOCX,
            ".mp3": FileType.AUDIO,
            ".wav": FileType.AUDIO,
            ".m4a": FileType.AUDIO,
            ".flac": FileType.AUDIO,
        }
        if suffix not in type_map:
            raise ValueError(f"Unsupported file type: {suffix}")
        return type_map[suffix]

    def _get_parser(self, file_type: FileType):
        """返回对应的解析函数."""
        parsers = {
            FileType.PDF: parse_pdf,
        }

        # 延迟导入可选解析器
        try:
            from src.parsers.ppt_parser import parse_pptx
            parsers[FileType.PPTX] = parse_pptx
        except ImportError:
            pass

        try:
            from src.parsers.note_parser import parse_note
            parsers[FileType.MARKDOWN] = parse_note
            parsers[FileType.TXT] = parse_note
            parsers[FileType.DOCX] = parse_note
        except ImportError:
            pass

        if file_type not in parsers:
            raise ValueError(f"No parser available for {file_type.value}")

        return parsers[file_type]

    def process(self, input_data: str | list[str]) -> list[ParsedDocument]:
        """解析一个或多个文件.

        Args:
            input_data: 文件路径或文件路径列表

        Returns:
            ParsedDocument 列表
        """
        if isinstance(input_data, str):
            input_data = [input_data]

        results: list[ParsedDocument] = []
        for file_path in input_data:
            path = Path(file_path)
            if not path.exists():
                logger.warning(f"File not found, skipping: {file_path}")
                continue

            file_type = self._detect_file_type(file_path)
            parser = self._get_parser(file_type)
            logger.info(f"Parsing [{file_type.value}]: {path.name}")

            doc = parser(file_path)
            results.append(doc)

        return results
