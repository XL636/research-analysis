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


SUPPORTED_EXTENSIONS = {".pdf", ".pptx", ".md", ".txt", ".docx"}


@app.command()
def batch(
    directory: str = typer.Argument(..., help="要批量处理的目录路径"),
    format: str = typer.Option("markdown", "--format", "-f", help="输出格式: markdown/docx/pptx"),
    synthesize: bool = typer.Option(False, "--synthesize", "-s", help="启用跨文档综合分析"),
    recursive: bool = typer.Option(False, "--recursive", "-r", help="递归扫描子目录"),
    output_dir: Optional[str] = typer.Option(None, "--output-dir", "-d", help="输出目录"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="显示详细日志"),
) -> None:
    """批量处理目录下的所有研究材料."""
    _setup_logging(verbose)

    dir_path = Path(directory)
    if not dir_path.is_dir():
        console.print(f"[red]目录不存在: {directory}[/red]")
        raise typer.Exit(1)

    # 扫描文件
    if recursive:
        files = [f for f in dir_path.rglob("*") if f.suffix.lower() in SUPPORTED_EXTENSIONS]
    else:
        files = [f for f in dir_path.iterdir() if f.is_file() and f.suffix.lower() in SUPPORTED_EXTENSIONS]

    if not files:
        console.print(f"[yellow]目录中没有找到支持的文件 ({', '.join(SUPPORTED_EXTENSIONS)})[/yellow]")
        raise typer.Exit(1)

    files.sort()
    console.print(f"\n[bold]📂 批量处理: 发现 {len(files)} 个文件[/bold]\n")
    for f in files:
        console.print(f"  • {f.relative_to(dir_path)}")
    console.print()

    from rich.progress import BarColumn, MofNCompleteColumn, Progress, TextColumn, TimeElapsedColumn

    from src.core.engine import Pipeline

    pipeline = Pipeline()

    # 设置输出目录
    out_dir = Path(output_dir) if output_dir else Path(pipeline.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    results: list[dict] = []
    with Progress(
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        MofNCompleteColumn(),
        TimeElapsedColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("批量分析", total=len(files))

        for file_path in files:
            progress.update(task, description=f"分析: {file_path.name}")
            try:
                ext_map = {"markdown": ".md", "docx": ".docx", "pptx": ".pptx"}
                ext = ext_map.get(format, ".md")
                out_path = str(out_dir / f"{file_path.stem}_report{ext}")

                ctx = pipeline.run(
                    input_files=[str(file_path)],
                    output_format=format,
                    output_path=out_path,
                    synthesize=False,
                )
                results.append({"file": file_path.name, "status": "success", "output": ctx.output_path})
            except Exception as e:
                logger.error(f"Failed to process {file_path}: {e}")
                results.append({"file": file_path.name, "status": "failed", "output": str(e)})
            progress.advance(task)

    # 综合分析（可选）
    if synthesize and len(files) > 1:
        console.print("\n[bold]🔄 生成综合分析...[/bold]")
        try:
            ext_map = {"markdown": ".md", "docx": ".docx", "pptx": ".pptx"}
            ext = ext_map.get(format, ".md")
            synth_path = str(out_dir / f"synthesis_report{ext}")

            ctx = pipeline.run(
                input_files=[str(f) for f in files],
                output_format=format,
                output_path=synth_path,
                synthesize=True,
            )
            results.append({"file": "[综合分析]", "status": "success", "output": ctx.output_path})
        except Exception as e:
            logger.error(f"Synthesis failed: {e}")
            results.append({"file": "[综合分析]", "status": "failed", "output": str(e)})

    # 汇总结果
    table = Table(title="批量处理结果")
    table.add_column("文件", style="cyan")
    table.add_column("状态", style="green")
    table.add_column("输出", style="dim")

    success_count = 0
    for r in results:
        status_style = "green" if r["status"] == "success" else "red"
        status_text = "✅ 成功" if r["status"] == "success" else "❌ 失败"
        if r["status"] == "success":
            success_count += 1
        table.add_row(r["file"], f"[{status_style}]{status_text}[/{status_style}]", r["output"])

    console.print()
    console.print(table)
    console.print(f"\n[bold]完成: {success_count}/{len(results)} 成功[/bold]")


@app.command(name="export")
def export_kb(
    format: str = typer.Option("json", "--format", "-f", help="导出格式: json/csv"),
    output: str = typer.Option("backup.json", "--output", "-o", help="输出文件路径"),
) -> None:
    """导出知识库数据."""
    from src.store.knowledge_base import KnowledgeBase

    kb = KnowledgeBase()

    if format == "csv":
        if not output.endswith(".csv"):
            output = output.rsplit(".", 1)[0] + ".csv"
        count = kb.export_csv(output)
    else:
        if not output.endswith(".json"):
            output = output.rsplit(".", 1)[0] + ".json"
        count = kb.export_json(output)

    console.print(f"[bold green]✅ 导出完成: {count} 篇文档 → {output}[/bold green]")


@app.command(name="import")
def import_kb(
    file: str = typer.Argument(..., help="要导入的 JSON 文件路径"),
) -> None:
    """从 JSON 文件导入数据到知识库."""
    file_path = Path(file)
    if not file_path.exists():
        console.print(f"[red]文件不存在: {file}[/red]")
        raise typer.Exit(1)

    if not file_path.suffix == ".json":
        console.print("[red]仅支持 JSON 格式导入[/red]")
        raise typer.Exit(1)

    from src.store.knowledge_base import KnowledgeBase

    kb = KnowledgeBase()
    count = kb.import_json(str(file_path))
    console.print(f"[bold green]✅ 导入完成: {count} 篇文档[/bold green]")


@app.command()
def serve(
    host: str = typer.Option("0.0.0.0", "--host", "-h", help="绑定地址"),
    port: int = typer.Option(8000, "--port", "-p", help="端口号"),
    reload: bool = typer.Option(False, "--reload", help="开发模式自动重载"),
) -> None:
    """启动 Web UI 服务."""
    try:
        import uvicorn
    except ImportError:
        console.print("[red]请先安装 web 依赖: uv sync --extra web[/red]")
        raise typer.Exit(1)

    console.print(f"\n[bold]Starting Research Analysis Web UI[/bold]")
    console.print(f"  API: http://{host}:{port}/docs")
    console.print(f"  UI:  http://{host}:{port}\n")

    uvicorn.run(
        "src.api.app:create_app",
        factory=True,
        host=host,
        port=port,
        reload=reload,
        reload_dirs=["src"] if reload else None,
    )


if __name__ == "__main__":
    app()
