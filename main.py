"""CLI 入口 - 研讨会/组会分析工具."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from loguru import logger
from rich.console import Console
from rich.table import Table

app = typer.Typer(
    name="research-analysis",
    help="研讨会/组会分析工具 - 从研究材料自动生成组会报告和结构化知识库",
)
console = Console()


def _setup_logging(verbose: bool = False) -> None:
    """配置日志."""
    import sys

    logger.remove()
    level = "DEBUG" if verbose else "INFO"
    logger.add(sys.stderr, level=level, format="<level>{message}</level>")


@app.command()
def analyze(
    files: list[str] = typer.Argument(..., help="要分析的文件路径（支持 PDF/PPTX/MD/TXT）"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="输出文件路径"),
    format: str = typer.Option("markdown", "--format", "-f", help="输出格式: markdown/docx/pptx"),
    synthesize: bool = typer.Option(False, "--synthesize", "-s", help="启用跨文档综合分析"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="显示详细日志"),
) -> None:
    """分析研究材料并生成报告."""
    _setup_logging(verbose)

    # 验证文件存在
    valid_files = []
    for f in files:
        path = Path(f)
        if not path.exists():
            console.print(f"[yellow]文件不存在，跳过: {f}[/yellow]")
            continue
        valid_files.append(str(path))

    if not valid_files:
        console.print("[red]没有可用的输入文件[/red]")
        raise typer.Exit(1)

    console.print(f"\n[bold]📚 开始分析 {len(valid_files)} 个文件[/bold]\n")

    from src.core.engine import Pipeline

    pipeline = Pipeline()
    ctx = pipeline.run(
        input_files=valid_files,
        output_format=format,
        output_path=output,
        synthesize=synthesize,
    )

    if ctx.output_path:
        console.print(f"\n[bold green]🎉 报告已生成: {ctx.output_path}[/bold green]")
    else:
        console.print("\n[red]报告生成失败[/red]")


@app.command()
def search(
    query: str = typer.Argument(..., help="搜索关键词"),
    limit: int = typer.Option(10, "--limit", "-n", help="最大结果数"),
) -> None:
    """搜索知识库."""
    try:
        from src.store.knowledge_base import KnowledgeBase
    except ImportError:
        console.print("[red]知识库模块未安装[/red]")
        raise typer.Exit(1)

    kb = KnowledgeBase()
    results = kb.search(query, limit=limit)

    if not results:
        console.print(f"[yellow]未找到与 '{query}' 相关的结果[/yellow]")
        return

    table = Table(title=f"搜索结果: {query}")
    table.add_column("标题", style="cyan")
    table.add_column("标签", style="green")
    table.add_column("日期", style="dim")

    for row in results:
        table.add_row(row["title"], row.get("tags", ""), row.get("date", ""))

    console.print(table)


@app.command(name="list")
def list_docs(
    tag: Optional[str] = typer.Option(None, "--tag", "-t", help="按标签筛选"),
    limit: int = typer.Option(20, "--limit", "-n", help="最大结果数"),
) -> None:
    """列出知识库中的所有文档."""
    try:
        from src.store.knowledge_base import KnowledgeBase
    except ImportError:
        console.print("[red]知识库模块未安装[/red]")
        raise typer.Exit(1)

    kb = KnowledgeBase()
    docs = kb.list_documents(tag=tag, limit=limit)

    if not docs:
        console.print("[yellow]知识库中暂无文档[/yellow]")
        return

    table = Table(title="知识库文档")
    table.add_column("ID", style="dim")
    table.add_column("标题", style="cyan")
    table.add_column("类型", style="green")
    table.add_column("标签", style="yellow")
    table.add_column("日期", style="dim")

    for doc in docs:
        table.add_row(
            str(doc["id"]),
            doc["title"],
            doc.get("file_type", ""),
            doc.get("tags", ""),
            doc.get("date", ""),
        )

    console.print(table)


if __name__ == "__main__":
    app()
