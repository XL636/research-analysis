"""Tests for batch, export, import CLI commands."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from main import app

runner = CliRunner()


# ---------------------------------------------------------------------------
# Batch command
# ---------------------------------------------------------------------------

class TestBatchCommand:
    """Tests for the 'batch' CLI command."""

    def test_batch_nonexistent_directory(self):
        result = runner.invoke(app, ["batch", "/nonexistent/dir"])
        assert result.exit_code != 0
        assert "目录不存在" in result.output

    def test_batch_empty_directory(self, tmp_path: Path):
        result = runner.invoke(app, ["batch", str(tmp_path)])
        assert result.exit_code != 0
        assert "没有找到支持的文件" in result.output

    def test_batch_finds_supported_files(self, tmp_path: Path):
        """Batch scans and processes supported files."""
        (tmp_path / "paper1.pdf").write_text("fake pdf")
        (tmp_path / "notes.md").write_text("# Notes")
        (tmp_path / "readme.txt").write_text("readme")
        (tmp_path / "image.png").write_text("not supported")

        mock_ctx = MagicMock()
        mock_ctx.output_path = str(tmp_path / "out.md")

        with patch("src.core.engine.Pipeline") as MockPipeline:
            MockPipeline.return_value.run.return_value = mock_ctx
            MockPipeline.return_value.output_dir = str(tmp_path / "output")
            result = runner.invoke(app, ["batch", str(tmp_path)])

        assert result.exit_code == 0
        # Should process 3 files (pdf, md, txt) but not png
        assert MockPipeline.return_value.run.call_count == 3
        assert "3/3 成功" in result.output

    def test_batch_recursive(self, tmp_path: Path):
        """--recursive scans subdirectories."""
        sub = tmp_path / "sub"
        sub.mkdir()
        (tmp_path / "a.pdf").write_text("pdf")
        (sub / "b.txt").write_text("txt")

        mock_ctx = MagicMock()
        mock_ctx.output_path = "out.md"

        with patch("src.core.engine.Pipeline") as MockPipeline:
            MockPipeline.return_value.run.return_value = mock_ctx
            MockPipeline.return_value.output_dir = str(tmp_path / "output")
            result = runner.invoke(app, ["batch", str(tmp_path), "--recursive"])

        assert result.exit_code == 0
        assert MockPipeline.return_value.run.call_count == 2

    def test_batch_with_output_dir(self, tmp_path: Path):
        """--output-dir specifies custom output directory."""
        (tmp_path / "paper.pdf").write_text("pdf")
        out_dir = tmp_path / "custom_output"

        mock_ctx = MagicMock()
        mock_ctx.output_path = str(out_dir / "paper_report.md")

        with patch("src.core.engine.Pipeline") as MockPipeline:
            MockPipeline.return_value.run.return_value = mock_ctx
            MockPipeline.return_value.output_dir = str(tmp_path / "output")
            result = runner.invoke(app, ["batch", str(tmp_path), "--output-dir", str(out_dir)])

        assert result.exit_code == 0
        assert out_dir.exists()

    def test_batch_with_synthesize(self, tmp_path: Path):
        """--synthesize generates a synthesis report after individual reports."""
        (tmp_path / "a.pdf").write_text("pdf")
        (tmp_path / "b.txt").write_text("txt")

        mock_ctx = MagicMock()
        mock_ctx.output_path = "out.md"

        with patch("src.core.engine.Pipeline") as MockPipeline:
            MockPipeline.return_value.run.return_value = mock_ctx
            MockPipeline.return_value.output_dir = str(tmp_path / "output")
            result = runner.invoke(app, ["batch", str(tmp_path), "--synthesize"])

        assert result.exit_code == 0
        # 2 individual files + 1 synthesis
        assert MockPipeline.return_value.run.call_count == 3

    def test_batch_handles_processing_failure(self, tmp_path: Path):
        """Failed file processing is reported but doesn't crash batch."""
        (tmp_path / "good.pdf").write_text("pdf")
        (tmp_path / "bad.txt").write_text("txt")

        call_count = 0

        def side_effect(**kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise RuntimeError("Parse failed")
            ctx = MagicMock()
            ctx.output_path = "out.md"
            return ctx

        with patch("src.core.engine.Pipeline") as MockPipeline:
            MockPipeline.return_value.run.side_effect = side_effect
            MockPipeline.return_value.output_dir = str(tmp_path / "output")
            result = runner.invoke(app, ["batch", str(tmp_path)])

        assert result.exit_code == 0
        assert "1/2 成功" in result.output


# ---------------------------------------------------------------------------
# Export command
# ---------------------------------------------------------------------------

class TestExportCommand:
    """Tests for the 'export' CLI command."""

    def test_export_json_default(self, tmp_path: Path):
        with patch("src.store.knowledge_base.KnowledgeBase") as MockKB:
            MockKB.return_value.export_json.return_value = 5
            result = runner.invoke(app, ["export", "--format", "json", "-o", str(tmp_path / "out.json")])
        assert result.exit_code == 0
        assert "5 篇文档" in result.output
        MockKB.return_value.export_json.assert_called_once()

    def test_export_csv(self, tmp_path: Path):
        with patch("src.store.knowledge_base.KnowledgeBase") as MockKB:
            MockKB.return_value.export_csv.return_value = 3
            result = runner.invoke(app, ["export", "--format", "csv", "-o", str(tmp_path / "out.csv")])
        assert result.exit_code == 0
        assert "3 篇文档" in result.output
        MockKB.return_value.export_csv.assert_called_once()


# ---------------------------------------------------------------------------
# Import command
# ---------------------------------------------------------------------------

class TestImportCommand:
    """Tests for the 'import' CLI command."""

    def test_import_nonexistent_file(self):
        result = runner.invoke(app, ["import", "/nonexistent/file.json"])
        assert result.exit_code != 0
        assert "文件不存在" in result.output

    def test_import_non_json_file(self, tmp_path: Path):
        csv_file = tmp_path / "data.csv"
        csv_file.write_text("a,b,c")
        result = runner.invoke(app, ["import", str(csv_file)])
        assert result.exit_code != 0
        assert "仅支持 JSON" in result.output

    def test_import_success(self, tmp_path: Path):
        json_file = tmp_path / "backup.json"
        json_file.write_text(json.dumps({"documents": []}))

        with patch("src.store.knowledge_base.KnowledgeBase") as MockKB:
            MockKB.return_value.import_json.return_value = 10
            result = runner.invoke(app, ["import", str(json_file)])

        assert result.exit_code == 0
        assert "10 篇文档" in result.output
