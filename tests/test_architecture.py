"""架构守护测试 — 用 AST 分析强制保证关键架构约束.

防止回归：
1. _try_download_pdf 必须使用 PaperDownloader
2. _fetch_pdf 必须检查 content-type
3. _fetch_pdf 必须验证 %PDF 魔数
4. _try_download_pdf 不能有 raw httpx.Client 调用

实现方式：
- 对于 paper_search.py（依赖 fastapi，可能未安装），直接读取源文件 + AST 分析
- 对于 paper_downloader.py（无特殊依赖），用 inspect.getsource + AST 分析
"""

import ast
import inspect
import textwrap
from pathlib import Path

from src.utils.paper_downloader import PaperDownloader

# paper_search.py 依赖 fastapi (optional)，不能直接 import；
# 改为从源文件读取再用 AST 提取目标函数。
_PAPER_SEARCH_PATH = Path(__file__).resolve().parent.parent / "src" / "api" / "routes" / "paper_search.py"


# ---------------------------------------------------------------------------
# 辅助函数
# ---------------------------------------------------------------------------

def _get_source_and_tree_from_func(func) -> tuple[str, ast.Module]:
    """从可导入的函数获取源码并解析为 AST."""
    source = inspect.getsource(func)
    tree = ast.parse(textwrap.dedent(source))
    return source, tree


def _get_function_source_from_file(filepath: Path, func_name: str) -> tuple[str, ast.Module]:
    """从源文件中提取指定函数的源码和 AST.

    用于无法直接 import 的模块（如依赖 fastapi 的文件）。
    """
    full_source = filepath.read_text(encoding="utf-8")
    module_tree = ast.parse(full_source)

    for node in ast.walk(module_tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == func_name:
            # 提取函数对应的源码行
            func_lines = full_source.splitlines()[node.lineno - 1 : node.end_lineno]
            func_source = "\n".join(func_lines)
            func_tree = ast.parse(textwrap.dedent(func_source))
            return func_source, func_tree

    raise ValueError(f"Function '{func_name}' not found in {filepath}")


def _find_all_names(tree: ast.Module) -> set[str]:
    """收集 AST 中出现的所有 Name 节点的 id."""
    return {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)}


def _find_all_attribute_chains(tree: ast.Module) -> list[str]:
    """收集 AST 中所有形如 a.b 的属性访问链（字符串列表）."""
    chains: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute):
            parts: list[str] = [node.attr]
            current = node.value
            while isinstance(current, ast.Attribute):
                parts.append(current.attr)
                current = current.value
            if isinstance(current, ast.Name):
                parts.append(current.id)
            parts.reverse()
            chains.append(".".join(parts))
    return chains


# ---------------------------------------------------------------------------
# 测试用例
# ---------------------------------------------------------------------------

class TestTryDownloadPdfArchitecture:
    """_try_download_pdf 的架构约束."""

    def test_try_download_pdf_uses_paper_downloader(self):
        """_try_download_pdf 必须使用 PaperDownloader，不能绕过."""
        _source, tree = _get_function_source_from_file(
            _PAPER_SEARCH_PATH, "_try_download_pdf",
        )
        all_names = _find_all_names(tree)

        assert "PaperDownloader" in all_names, (
            "_try_download_pdf must use PaperDownloader, not raw HTTP calls / "
            "_try_download_pdf 必须使用 PaperDownloader，不能直接发 HTTP 请求"
        )

    def test_try_download_pdf_no_raw_httpx(self):
        """_try_download_pdf 不能直接调用 httpx.Client 或 httpx.get."""
        _source, tree = _get_function_source_from_file(
            _PAPER_SEARCH_PATH, "_try_download_pdf",
        )
        attr_chains = _find_all_attribute_chains(tree)

        # 禁止的模式：httpx.Client、httpx.get、httpx.AsyncClient 等
        forbidden = {"httpx.Client", "httpx.AsyncClient", "httpx.get", "httpx.post"}
        found = forbidden & set(attr_chains)

        assert not found, (
            f"_try_download_pdf should delegate to PaperDownloader, not call httpx directly / "
            f"_try_download_pdf 应委托 PaperDownloader，不应直接调用 httpx "
            f"(发现: {found})"
        )


class TestFetchPdfArchitecture:
    """PaperDownloader._fetch_pdf 的架构约束."""

    def test_fetch_pdf_checks_content_type(self):
        """_fetch_pdf 必须检查 content-type 以拒绝 HTML 响应."""
        source, _ = _get_source_and_tree_from_func(PaperDownloader._fetch_pdf)

        # content-type 检查可以是 headers.get("content-type") 或 content_type 变量
        has_content_type_check = (
            "content-type" in source or "content_type" in source
        )

        assert has_content_type_check, (
            "_fetch_pdf must check content-type to reject HTML responses / "
            "_fetch_pdf 必须检查 content-type 以拒绝 HTML 响应"
        )

    def test_fetch_pdf_validates_pdf_magic(self):
        """_fetch_pdf 必须验证 %PDF 魔数."""
        source, _ = _get_source_and_tree_from_func(PaperDownloader._fetch_pdf)

        assert "%PDF" in source, (
            "_fetch_pdf must validate %PDF magic bytes / "
            "_fetch_pdf 必须验证 %PDF 魔数以确保下载的是真正的 PDF 文件"
        )
