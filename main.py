"""CLI 入口 - 研讨会/组会分析工具."""

from __future__ import annotations

import json as json_lib
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
    template_id: Optional[int] = typer.Option(None, "--template-id", help="使用数据库中的模板 ID"),
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

    # 加载数据库模板
    template_content = None
    if template_id is not None:
        from src.store.template_store import TemplateStore
        store = TemplateStore()
        tpl = store.get_template(template_id)
        if not tpl:
            console.print(f"[red]模板不存在: id={template_id}[/red]")
            raise typer.Exit(1)
        template_content = tpl.prompt_content
        console.print(f"\n[bold]📚 开始分析 {len(valid_files)} 个文件 (模板: {tpl.display_name})[/bold]\n")
    elif mode:
        mode_label = ANALYSIS_MODE_LABELS.get(mode, mode)
        console.print(f"\n[bold]📚 开始分析 {len(valid_files)} 个文件 (模式: {mode_label})[/bold]\n")
    else:
        template_label = "会议报告" if template == "meeting" else "标准报告"
        console.print(f"\n[bold]📚 开始分析 {len(valid_files)} 个文件 (模板: {template_label})[/bold]\n")

    from src.core.engine import Pipeline

    pipeline = Pipeline(template=template, mode=mode, template_content=template_content)
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
    json_output: bool = typer.Option(False, "--json", help="JSON 格式输出（供程序化读取）"),
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
        if json_output:
            print("[]")
        else:
            console.print(f"[yellow]未找到与 '{query}' 相关的结果[/yellow]")
        return

    if json_output:
        print(json_lib.dumps(results, ensure_ascii=False, indent=2))
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
    concurrency: int = typer.Option(0, "--concurrency", "-c", help="并行文件数（0=使用配置默认值）"),
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

    from concurrent.futures import ThreadPoolExecutor, as_completed as futures_as_completed

    import yaml
    from rich.progress import BarColumn, MofNCompleteColumn, Progress, TextColumn, TimeElapsedColumn

    from src.core.engine import Pipeline

    # 确定并发数
    if concurrency <= 0:
        try:
            with open("config/settings.yaml", encoding="utf-8") as f:
                cfg = yaml.safe_load(f)
            concurrency = cfg.get("pipeline", {}).get("batch_max_concurrency", 5)
        except Exception:
            concurrency = 5

    # 设置输出目录
    sample_pipeline = Pipeline(template=template, mode=mode)
    out_dir = Path(output_dir) if output_dir else Path(sample_pipeline.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    def process_one(file_path: Path) -> dict:
        """处理单个文件（在线程中运行）."""
        try:
            ext_map = {"markdown": ".md", "docx": ".docx", "pptx": ".pptx", "pdf": ".pdf"}
            ext = ext_map.get(format, ".md")
            out_path = str(out_dir / f"{file_path.stem}_report{ext}")

            p = Pipeline(template=template, mode=mode)
            ctx = p.run(
                input_files=[str(file_path)],
                output_format=format,
                output_path=out_path,
                synthesize=False,
            )
            return {"file": file_path.name, "status": "success", "output": ctx.output_path}
        except Exception as e:
            logger.error(f"Failed to process {file_path}: {e}")
            return {"file": file_path.name, "status": "failed", "output": str(e)}

    results: list[dict] = []
    with Progress(
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        MofNCompleteColumn(),
        TimeElapsedColumn(),
        console=console,
    ) as progress:
        task = progress.add_task(f"批量分析 (并发={concurrency})", total=len(files))

        with ThreadPoolExecutor(max_workers=concurrency) as executor:
            future_to_file = {executor.submit(process_one, fp): fp for fp in files}

            for future in futures_as_completed(future_to_file):
                fp = future_to_file[future]
                result = future.result()
                results.append(result)
                status = "✅" if result["status"] == "success" else "❌"
                progress.update(task, description=f"{status} {fp.name}")
                progress.advance(task)

    # 综合分析（可选）
    if synthesize and len(files) > 1:
        console.print("\n[bold]🔄 生成综合分析...[/bold]")
        try:
            ext_map = {"markdown": ".md", "docx": ".docx", "pptx": ".pptx"}
            ext = ext_map.get(format, ".md")
            synth_path = str(out_dir / f"synthesis_report{ext}")

            p = Pipeline(template=template, mode=mode)
            ctx = p.run(
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


# ── Template 子命令组 ──

template_app = typer.Typer(name="template", help="报告模板管理 - 查看/创建/删除报告模板")
app.add_typer(template_app, name="template")


@template_app.command(name="list")
def template_list() -> None:
    """列出所有报告模板."""
    from src.store.template_store import TemplateStore

    store = TemplateStore()
    templates = store.list_templates()

    if not templates:
        console.print("[yellow]暂无模板[/yellow]")
        return

    table = Table(title="报告模板")
    table.add_column("ID", style="dim")
    table.add_column("名称", style="cyan")
    table.add_column("显示名", style="bold")
    table.add_column("类型", style="green")
    table.add_column("描述")

    for t in templates:
        ttype = "内置" if t.is_builtin else "自定义"
        table.add_row(str(t.id), t.name, t.display_name, ttype, t.description)

    console.print(table)


@template_app.command(name="show")
def template_show(
    template_id: int = typer.Argument(..., help="模板 ID"),
) -> None:
    """查看模板详情."""
    from src.store.template_store import TemplateStore

    store = TemplateStore()
    t = store.get_template(template_id)
    if not t:
        console.print(f"[red]模板不存在: id={template_id}[/red]")
        raise typer.Exit(1)

    console.print(f"\n[bold]{t.display_name}[/bold] ({t.name})")
    console.print(f"  ID: {t.id}")
    console.print(f"  类型: {'内置' if t.is_builtin else '自定义'}")
    console.print(f"  描述: {t.description}")
    if t.sections:
        console.print("  章节:")
        for s in t.sections:
            req = "必填" if s.required else "可选"
            console.print(f"    - {s.title} ({req}) {s.description}")
    console.print(f"\n[dim]Prompt 内容 ({len(t.prompt_content)} 字符):[/dim]")
    # 只显示前 500 字符
    preview = t.prompt_content[:500]
    if len(t.prompt_content) > 500:
        preview += "..."
    console.print(preview)


@template_app.command(name="create")
def template_create(
    name: str = typer.Option(..., "--name", "-n", help="模板唯一名称 (slug)"),
    display_name: str = typer.Option("", "--display-name", "-d", help="显示名称"),
    description: str = typer.Option("", "--desc", help="模板描述"),
    file: Optional[str] = typer.Option(None, "--file", "-f", help="从文件读取 prompt 内容"),
    prompt: str = typer.Option("", "--prompt", "-p", help="直接指定 prompt 内容"),
) -> None:
    """创建自定义模板."""
    from src.store.template_store import TemplateStore

    if not display_name:
        display_name = name

    prompt_content = prompt
    if file:
        file_path = Path(file)
        if not file_path.exists():
            console.print(f"[red]文件不存在: {file}[/red]")
            raise typer.Exit(1)
        prompt_content = file_path.read_text(encoding="utf-8")

    if not prompt_content:
        console.print("[red]请通过 --file 或 --prompt 提供 prompt 内容[/red]")
        raise typer.Exit(1)

    store = TemplateStore()
    try:
        t = store.create_template(
            name=name,
            display_name=display_name,
            description=description,
            prompt_content=prompt_content,
        )
        console.print(f"[bold green]模板已创建: {t.display_name} (id={t.id})[/bold green]")
    except Exception as e:
        console.print(f"[red]创建失败: {e}[/red]")
        raise typer.Exit(1)


@template_app.command(name="delete")
def template_delete(
    template_id: int = typer.Argument(..., help="模板 ID"),
) -> None:
    """删除自定义模板（内置模板不可删除）."""
    from src.store.template_store import TemplateStore

    store = TemplateStore()
    try:
        success = store.delete_template(template_id)
        if success:
            console.print(f"[bold green]模板已删除: id={template_id}[/bold green]")
        else:
            console.print(f"[red]模板不存在: id={template_id}[/red]")
    except ValueError as e:
        console.print(f"[red]{e}[/red]")
        raise typer.Exit(1)


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


@app.command(name="store-analysis")
def store_analysis_cli(
    json_file: str = typer.Argument(..., help="AnalysisResult JSON 文件路径"),
    source: str = typer.Option("", "--source", "-s", help="源文件路径"),
    type: str = typer.Option("pdf", "--type", "-t", help="文件类型"),
    source_type: str = typer.Option("claude_analysis", "--source-type", help="来源类型"),
) -> None:
    """将 JSON 分析结果存入知识库（供 Claude Code Skill 调用）."""
    json_path = Path(json_file)
    if not json_path.exists():
        console.print(f"[red]JSON 文件不存在: {json_file}[/red]")
        raise typer.Exit(1)

    from src.core.models import AnalysisResult
    from src.store.knowledge_base import KnowledgeBase

    try:
        raw = json_lib.loads(json_path.read_text(encoding="utf-8"))
        analysis = AnalysisResult.model_validate(raw)
    except Exception as e:
        console.print(f"[red]JSON 解析失败: {e}[/red]")
        raise typer.Exit(1)

    kb = KnowledgeBase()
    doc_id = kb.store_analysis(analysis, file_path=source, file_type=type, source_type=source_type)
    console.print(f"[bold green]已存入知识库: doc_id={doc_id}[/bold green]")


@app.command(name="get-analysis")
def get_analysis_cli(
    doc_id: int = typer.Argument(..., help="文档 ID"),
) -> None:
    """获取单篇文档的完整分析 JSON（供 Claude Code Skill 调用）."""
    from src.store.knowledge_base import KnowledgeBase

    kb = KnowledgeBase()
    analysis = kb.get_analysis(doc_id)

    if not analysis:
        console.print(f"[red]未找到文档 ID={doc_id} 的分析结果[/red]")
        raise typer.Exit(1)

    print(analysis.model_dump_json(indent=2))


@app.command(name="paper-search")
def paper_search(
    query: str = typer.Argument(..., help="搜索关键词"),
    providers: Optional[str] = typer.Option(None, "--providers", "-p", help="搜索源，逗号分隔 (如 arxiv,pubmed,biorxiv,semantic_scholar,openalex)"),
    limit: int = typer.Option(5, "--limit", "-n", help="每个搜索源的最大结果数"),
    save: bool = typer.Option(False, "--save", "-s", help="将结果保存到知识库"),
    json_output: bool = typer.Option(False, "--json", help="JSON 格式输出"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="显示详细日志"),
) -> None:
    """搜索外部学术论文 (PubMed, arXiv, bioRxiv, Semantic Scholar, OpenAlex)."""
    _setup_logging(verbose)

    from src.core.search_client import SearchManager

    sm = SearchManager()

    provider_names = None
    if providers:
        provider_names = [p.strip() for p in providers.split(",") if p.strip()]

    if not sm.has_providers:
        console.print("[red]没有可用的搜索源，请检查 config/settings.yaml[/red]")
        raise typer.Exit(1)

    if not json_output:
        console.print(f"\n[bold]搜索论文: {query}[/bold]")
        if provider_names:
            console.print(f"[dim]搜索源: {', '.join(provider_names)}[/dim]")

    try:
        results = sm.search(query, max_results=limit, provider_names=provider_names)
    finally:
        sm.close()

    if not results:
        if json_output:
            print("[]")
        else:
            console.print("[yellow]未找到相关论文[/yellow]")
        return

    if json_output:
        data = [r.model_dump() for r in results]
        print(json_lib.dumps(data, ensure_ascii=False, indent=2))
        if save:
            _save_search_results_to_kb(results)
        return

    # Rich Table output
    table = Table(title=f"论文搜索结果 ({len(results)} 条)")
    table.add_column("#", style="dim", width=3)
    table.add_column("标题", style="cyan", max_width=50)
    table.add_column("作者", style="dim", max_width=30)
    table.add_column("年份", style="green", width=5)
    table.add_column("来源", style="magenta", width=10)
    table.add_column("URL", style="blue", max_width=40)

    for i, r in enumerate(results, 1):
        # Truncate title for table display
        title = r.title[:48] + "..." if len(r.title) > 50 else r.title
        authors = r.authors[:28] + "..." if len(r.authors) > 30 else r.authors
        url = r.url[:38] + "..." if len(r.url) > 40 else r.url
        source_label = {
            "pubmed": "PubMed",
            "arxiv": "arXiv",
            "biorxiv": "bioRxiv",
            "medrxiv": "medRxiv",
            "semantic_scholar": "S2",
            "openalex": "OpenAlex",
            "crossref": "CrossRef",
        }.get(r.source, r.source)
        table.add_row(str(i), title, authors, r.year, source_label, url)

    console.print(table)

    if save:
        saved = _save_search_results_to_kb(results)
        console.print(f"\n[bold green]已保存 {saved} 条结果到知识库[/bold green]")


@app.command(name="smart-search")
def smart_search(
    query: str = typer.Argument(..., help="研究问题或主题描述（支持中英文）"),
    providers: Optional[str] = typer.Option(None, "--providers", "-p", help="搜索源，逗号分隔 (如 arxiv,pubmed,semantic_scholar)"),
    limit: int = typer.Option(20, "--limit", "-n", help="最大返回结果数"),
    save: bool = typer.Option(False, "--save", "-s", help="将结果保存到知识库"),
    json_output: bool = typer.Option(False, "--json", help="JSON 格式输出"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="显示详细日志"),
) -> None:
    """智能论文搜索 - LLM 理解意图 + 自动生成关键词 + 多源搜索 + 智能排序."""
    _setup_logging(verbose)

    from src.agents.paper_search import PaperSearchAgent, SmartSearchInput
    from src.core.llm_client import LLMClient
    from src.core.search_client import SearchManager

    llm = LLMClient()
    sm = SearchManager()

    if not sm.has_providers:
        console.print("[red]没有可用的搜索源，请检查 config/settings.yaml[/red]")
        raise typer.Exit(1)

    provider_names = None
    if providers:
        provider_names = [p.strip() for p in providers.split(",") if p.strip()]

    agent = PaperSearchAgent(llm_client=llm, search_manager=sm)
    search_input = SmartSearchInput(
        query=query,
        providers=provider_names,
        max_results=limit,
    )

    if not json_output:
        console.print(f"\n[bold]智能搜索: {query}[/bold]")
        console.print("[dim]正在分析意图并生成关键词...[/dim]")

    try:
        output = agent.process(search_input)
    finally:
        sm.close()

    if json_output:
        print(json_lib.dumps(output.model_dump(), ensure_ascii=False, indent=2))
        if save and output.results:
            _save_smart_results_to_kb(output.results)
        return

    # 显示意图和关键词
    console.print(f"\n[bold cyan]理解意图:[/bold cyan] {output.interpreted_intent}")
    if output.domain_detected:
        console.print(f"[bold cyan]检测领域:[/bold cyan] {output.domain_detected}")
    console.print(f"[bold cyan]生成关键词:[/bold cyan] {', '.join(output.generated_keywords)}")
    stats_parts = [
        f"候选论文: {output.total_candidates} 篇",
        f"筛选后: {len(output.results)} 篇",
        f"搜索源: {', '.join(output.providers_used)}",
    ]
    if output.iterations_used > 1:
        stats_parts.append(f"迭代: {output.iterations_used} 轮")
    if output.quality_score > 0:
        stats_parts.append(f"质量: {output.quality_score:.0%}")
    console.print(f"[dim]{' | '.join(stats_parts)}[/dim]\n")

    if not output.results:
        console.print("[yellow]未找到相关论文[/yellow]")
        return

    # Rich Table 输出
    table = Table(title=f"智能搜索结果 ({len(output.results)} 条)")
    table.add_column("#", style="dim", width=3)
    table.add_column("评分", width=5)
    table.add_column("标题", style="cyan", max_width=45)
    table.add_column("年份", style="green", width=5)
    table.add_column("来源", style="magenta", width=10)
    table.add_column("相关性", style="dim", max_width=35)

    for i, r in enumerate(output.results, 1):
        # 评分颜色
        score = r.relevance_score
        if score >= 0.8:
            score_str = f"[bold green]{score:.1f}[/bold green]"
        elif score >= 0.5:
            score_str = f"[yellow]{score:.1f}[/yellow]"
        else:
            score_str = f"[dim]{score:.1f}[/dim]"

        title = r.title[:43] + "..." if len(r.title) > 45 else r.title
        reason = r.relevance_reason[:33] + "..." if len(r.relevance_reason) > 35 else r.relevance_reason
        source_label = {
            "pubmed": "PubMed",
            "arxiv": "arXiv",
            "biorxiv": "bioRxiv",
            "medrxiv": "medRxiv",
            "semantic_scholar": "S2",
            "openalex": "OpenAlex",
            "crossref": "CrossRef",
        }.get(r.source, r.source)
        table.add_row(str(i), score_str, title, r.year, source_label, reason)

    console.print(table)

    # T-87: 中文数据库快捷链接
    if output.chinese_db_links:
        console.print("\n[bold amber]中文数据库快捷搜索:[/bold amber]")
        for link in output.chinese_db_links:
            console.print(f"  [blue]{link['name']}[/blue]: {link['url']}")

    if save:
        saved = _save_smart_results_to_kb(output.results)
        console.print(f"\n[bold green]已保存 {saved} 条结果到知识库[/bold green]")


def _save_smart_results_to_kb(results) -> int:
    """Save smart search results to knowledge base."""
    from src.store.knowledge_base import KnowledgeBase

    kb = KnowledgeBase()
    saved = 0
    for r in results:
        try:
            kb.store_metadata_only(
                title=r.title,
                summary=r.abstract,
                doi=r.doi,
                url=r.url,
                authors=r.authors,
                year=r.year,
                source_type="smart_search",
            )
            saved += 1
        except Exception as e:
            logger.warning(f"Failed to save '{r.title}': {e}")
    return saved


def _save_search_results_to_kb(results) -> int:
    """Save search results to knowledge base."""
    from src.store.knowledge_base import KnowledgeBase

    kb = KnowledgeBase()
    saved = 0
    for r in results:
        try:
            kb.store_metadata_only(
                title=r.title,
                summary=r.abstract,
                doi=r.doi,
                url=r.url,
                authors=r.authors,
                year=r.year,
                source_type="paper_search",
            )
            saved += 1
        except Exception as e:
            logger.warning(f"Failed to save '{r.title}': {e}")
    return saved


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
