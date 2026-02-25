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


ANALYSIS_MODE_LABELS = {
    "quick": "快速摘要",
    "standard": "标准分析",
    "deep": "深度研究",
    "meeting": "会议报告",
}


@app.command()
def analyze(
    files: list[str] = typer.Argument(..., help="要分析的文件路径（支持 PDF/PPTX/MD/TXT）"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="输出文件路径"),
    format: str = typer.Option("markdown", "--format", "-f", help="输出格式: markdown/docx/pptx/pdf"),
    template: str = typer.Option("default", "--template", "-t", help="报告模板: default/meeting"),
    mode: Optional[str] = typer.Option(None, "--mode", "-m", help="分析模式: quick/standard/deep/meeting"),
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

    # --mode 优先于 --template
    if mode:
        mode_label = ANALYSIS_MODE_LABELS.get(mode, mode)
        console.print(f"\n[bold]📚 开始分析 {len(valid_files)} 个文件 (模式: {mode_label})[/bold]\n")
    else:
        template_label = "会议报告" if template == "meeting" else "标准报告"
        console.print(f"\n[bold]📚 开始分析 {len(valid_files)} 个文件 (模板: {template_label})[/bold]\n")

    from src.core.engine import Pipeline

    pipeline = Pipeline(template=template, mode=mode)
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
    format: str = typer.Option("markdown", "--format", "-f", help="输出格式: markdown/docx/pptx/pdf"),
    template: str = typer.Option("default", "--template", "-t", help="报告模板: default/meeting"),
    mode: Optional[str] = typer.Option(None, "--mode", "-m", help="分析模式: quick/standard/deep/meeting"),
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

    pipeline = Pipeline(template=template, mode=mode)

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
                ext_map = {"markdown": ".md", "docx": ".docx", "pptx": ".pptx", "pdf": ".pdf"}
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


# ── Paper 子命令组 ──

paper_app = typer.Typer(name="paper", help="论文写作工具 - 交互式生成学术论文")
app.add_typer(paper_app, name="paper")


@paper_app.command(name="new")
def paper_new(
    name: str = typer.Argument(..., help="论文名称/标题"),
    topic: str = typer.Option("", "--topic", "-t", help="研究主题"),
    lang: str = typer.Option("zh", "--lang", "-l", help="语言: zh/en"),
    venue: str = typer.Option("generic", "--venue", help="目标会议: generic/neurips/icml/iclr/acl/aaai/colm/chinese_journal"),
    question: str = typer.Option("", "--question", "-q", help="研究问题"),
    words: int = typer.Option(8000, "--words", "-w", help="目标字数"),
    ref: Optional[list[int]] = typer.Option(None, "--ref", "-r", help="引用的知识库文档 ID"),
    context: str = typer.Option("", "--context", "-c", help="补充说明"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="显示详细日志"),
) -> None:
    """创建论文项目并自动生成大纲."""
    _setup_logging(verbose)

    from src.core.paper_models import PaperLanguage, PaperVenue
    from src.core.writer_engine import WriterPipeline

    wp = WriterPipeline()
    project = wp.create_project(
        name=name,
        topic=topic,
        language=PaperLanguage(lang),
        venue=PaperVenue(venue),
        research_question=question,
        target_word_count=words,
        reference_doc_ids=ref or [],
        additional_context=context,
    )
    console.print(f"\n[bold green]项目已创建: {project.id}[/bold green]")

    # 自动生成大纲
    project = wp.generate_outline(project)
    _print_outline(project)
    console.print(f"\n[dim]使用 'paper outline {project.id} --action confirm' 确认大纲[/dim]")


@paper_app.command(name="outline")
def paper_outline(
    project_id: str = typer.Argument(..., help="项目 ID"),
    action: str = typer.Option("show", "--action", "-a", help="操作: show/revise/confirm"),
    feedback: str = typer.Option("", "--feedback", "-f", help="修改反馈（revise 时使用）"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="显示详细日志"),
) -> None:
    """查看/修改/确认论文大纲."""
    _setup_logging(verbose)

    from src.core.writer_engine import WriterPipeline

    wp = WriterPipeline()
    project = wp.store.load(project_id)
    if not project:
        console.print(f"[red]项目不存在: {project_id}[/red]")
        raise typer.Exit(1)

    if action == "show":
        _print_outline(project)
    elif action == "revise":
        if not feedback:
            console.print("[red]修改大纲需要 --feedback 参数[/red]")
            raise typer.Exit(1)
        project = wp.revise_outline(project, feedback)
        _print_outline(project)
    elif action == "confirm":
        project = wp.confirm_outline(project)
        console.print("[bold green]大纲已确认，可以开始写作[/bold green]")
        console.print(f"[dim]使用 'paper write {project.id}' 开始写作[/dim]")
    else:
        console.print(f"[red]未知操作: {action}[/red]")
        raise typer.Exit(1)


@paper_app.command(name="write")
def paper_write(
    project_id: str = typer.Argument(..., help="项目 ID"),
    section: Optional[str] = typer.Option(None, "--section", "-s", help="指定章节 ID（不指定则写全部）"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="显示详细日志"),
) -> None:
    """写作论文章节."""
    _setup_logging(verbose)

    from src.core.writer_engine import WriterPipeline

    wp = WriterPipeline()
    project = wp.store.load(project_id)
    if not project:
        console.print(f"[red]项目不存在: {project_id}[/red]")
        raise typer.Exit(1)

    if section:
        project = wp.write_section(project, section)
        console.print(f"[bold green]章节 {section} 写作完成[/bold green]")
    else:
        project = wp.write_all_sections(project)
        console.print("[bold green]全部章节写作完成[/bold green]")

    console.print(f"[dim]使用 'paper status {project.id}' 查看进度[/dim]")


@paper_app.command(name="revise")
def paper_revise(
    project_id: str = typer.Argument(..., help="项目 ID"),
    section_id: str = typer.Argument(..., help="章节 ID"),
    feedback: str = typer.Option(..., "--feedback", "-f", help="修改要求"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="显示详细日志"),
) -> None:
    """修改论文章节."""
    _setup_logging(verbose)

    from src.core.writer_engine import WriterPipeline

    wp = WriterPipeline()
    project = wp.store.load(project_id)
    if not project:
        console.print(f"[red]项目不存在: {project_id}[/red]")
        raise typer.Exit(1)

    project = wp.revise_section(project, section_id, feedback)
    console.print(f"[bold green]章节 {section_id} 修改完成[/bold green]")


@paper_app.command(name="polish")
def paper_polish(
    project_id: str = typer.Argument(..., help="项目 ID"),
    instructions: str = typer.Option("", "--instructions", "-i", help="特别润色要求"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="显示详细日志"),
) -> None:
    """全文润色."""
    _setup_logging(verbose)

    from src.core.writer_engine import WriterPipeline

    wp = WriterPipeline()
    project = wp.store.load(project_id)
    if not project:
        console.print(f"[red]项目不存在: {project_id}[/red]")
        raise typer.Exit(1)

    project = wp.polish(project, instructions)
    console.print("[bold green]全文润色完成[/bold green]")


@paper_app.command(name="export")
def paper_export(
    project_id: str = typer.Argument(..., help="项目 ID"),
    format: str = typer.Option("markdown", "--format", "-f", help="输出格式: markdown/docx/pdf/latex"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="输出路径"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="显示详细日志"),
) -> None:
    """导出论文."""
    _setup_logging(verbose)

    from src.core.writer_engine import WriterPipeline

    wp = WriterPipeline()
    project = wp.store.load(project_id)
    if not project:
        console.print(f"[red]项目不存在: {project_id}[/red]")
        raise typer.Exit(1)

    result = wp.export(project, fmt=format, output_path=output or "")
    console.print(f"[bold green]论文已导出: {result}[/bold green]")


@paper_app.command(name="list")
def paper_list(
    limit: int = typer.Option(20, "--limit", "-n", help="最大结果数"),
) -> None:
    """列出所有论文项目."""
    from src.store.paper_store import PaperStore

    store = PaperStore()
    projects = store.list_projects(limit=limit)

    if not projects:
        console.print("[yellow]暂无论文项目[/yellow]")
        return

    table = Table(title="论文项目")
    table.add_column("ID", style="dim")
    table.add_column("名称", style="cyan")
    table.add_column("状态", style="green")
    table.add_column("更新时间", style="dim")

    for p in projects:
        table.add_row(p["id"], p["name"], p["status"], p["updated_at"])

    console.print(table)


@paper_app.command(name="status")
def paper_status(
    project_id: str = typer.Argument(..., help="项目 ID"),
) -> None:
    """查看论文项目状态."""
    from src.store.paper_store import PaperStore

    store = PaperStore()
    project = store.load(project_id)
    if not project:
        console.print(f"[red]项目不存在: {project_id}[/red]")
        raise typer.Exit(1)

    console.print(f"\n[bold]{project.name}[/bold]")
    console.print(f"  ID: {project.id}")
    console.print(f"  状态: {project.status.value}")
    console.print(f"  语言: {project.language.value}")
    console.print(f"  目标字数: {project.target_word_count}")
    console.print(f"  引用数: {len(project.citations)}")

    if project.draft:
        console.print(f"  当前字数: {project.draft.total_word_count}")
        console.print(f"\n  [bold]章节进度:[/bold]")
        for s in project.draft.sections:
            status_icon = {"pending": "⏳", "writing": "✏️", "draft": "📝", "revising": "🔄", "done": "✅"}.get(s.status.value, "❓")
            console.print(f"    {status_icon} [{s.id}] {s.title} ({s.word_count} 字)")


def _print_outline(project) -> None:
    """打印论文大纲."""
    if not project.outline:
        console.print("[yellow]暂无大纲[/yellow]")
        return

    outline = project.outline
    console.print(f"\n[bold]论文大纲: {project.name}[/bold]")

    if outline.abstract_draft:
        console.print(f"\n[dim]摘要草稿:[/dim]\n{outline.abstract_draft}")

    console.print(f"\n[dim]预估字数: {outline.estimated_word_count}[/dim]")
    console.print(f"\n[bold]章节结构:[/bold]")

    for s in outline.sections:
        indent = "  " * s.level
        console.print(f"{indent}[cyan]{s.id}[/cyan] {s.title} ({s.word_count} 字)")
        for point in s.outline_points:
            console.print(f"{indent}  - {point}")


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
