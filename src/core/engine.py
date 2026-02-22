"""Pipeline 工作流引擎 - 串联各 Agent 执行分析流程."""

from __future__ import annotations

from pathlib import Path

import yaml
from loguru import logger
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from src.agents.analyzer import AnalyzerAgent
from src.agents.generator import GeneratorAgent
from src.agents.parser import ParserAgent
from src.core.llm_client import LLMClient
from src.core.models import PipelineContext, UsageStats
from src.outputs.markdown_writer import write_markdown

console = Console()


class Pipeline:
    """分析 Pipeline：Parse → Analyze → [Synthesize] → Generate → [Review]."""

    def __init__(self, config_path: str = "config/settings.yaml", template: str = "default"):
        self.config_path = config_path
        self.llm = LLMClient(config_path)

        # 加载 pipeline 配置
        with open(config_path, encoding="utf-8") as f:
            config = yaml.safe_load(f)
        pipeline_conf = config.get("pipeline", {})
        self.max_review_retries = pipeline_conf.get("max_review_retries", 2)
        self.output_dir = pipeline_conf.get("output_dir", "./output")

        # 初始化 Agent
        self.parser = ParserAgent(self.llm, config_path)
        self.analyzer = AnalyzerAgent(self.llm, config_path)
        self.generator = GeneratorAgent(self.llm, config_path, template=template)

    def run(
        self,
        input_files: list[str],
        output_format: str = "markdown",
        output_path: str | None = None,
        synthesize: bool = False,
    ) -> PipelineContext:
        """执行完整的分析 Pipeline.

        Args:
            input_files: 输入文件路径列表
            output_format: 输出格式（markdown/docx/pptx）
            output_path: 输出文件路径（可选）
            synthesize: 是否进行跨文档综合分析

        Returns:
            Pipeline 执行上下文
        """
        ctx = PipelineContext(
            input_files=input_files,
            output_format=output_format,
        )

        # 多文档自动启用综合分析
        if len(input_files) > 1:
            synthesize = True

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            # Step 1: Parse
            task = progress.add_task("📄 解析文档...", total=None)
            ctx.parsed_documents = self.parser.process(input_files)
            if not ctx.parsed_documents:
                console.print("[red]未能解析任何文档[/red]")
                return ctx
            progress.update(task, description=f"✅ 解析完成 ({len(ctx.parsed_documents)} 篇)")

            # Step 2: Analyze
            task = progress.add_task("🔍 深度分析...", total=None)
            for doc in ctx.parsed_documents:
                analysis = self.analyzer.process(doc)
                ctx.analyses.append(analysis)
                # 存入知识库
                try:
                    from src.store.knowledge_base import KnowledgeBase
                    kb = KnowledgeBase()
                    kb.store_analysis(analysis, file_path=doc.file_path, file_type=doc.file_type.value)
                except Exception:
                    pass  # 知识库存储失败不影响主流程
            progress.update(task, description=f"✅ 分析完成 ({len(ctx.analyses)} 篇)")

            # Step 3: Synthesize (optional)
            if synthesize and len(ctx.analyses) > 1:
                task = progress.add_task("🔄 跨文档综合...", total=None)
                try:
                    from src.agents.synthesizer import SynthesizerAgent
                    synthesizer = SynthesizerAgent(self.llm, self.config_path)
                    ctx.synthesis = synthesizer.process(ctx.analyses)
                    progress.update(task, description="✅ 综合分析完成")
                except ImportError:
                    progress.update(task, description="⏭️ 综合分析未启用")

            # Step 4: Generate
            task = progress.add_task("📝 生成报告...", total=None)
            generator_input = ctx.synthesis if ctx.synthesis else ctx.analyses
            ctx.report = self.generator.process(generator_input)
            progress.update(task, description="✅ 报告生成完成")

            # Step 5: Review (optional)
            try:
                from src.agents.reviewer import ReviewerAgent
                reviewer = ReviewerAgent(self.llm, self.config_path)

                for attempt in range(self.max_review_retries + 1):
                    task = progress.add_task(
                        f"🔎 质量评审 (第 {attempt + 1} 轮)...", total=None,
                    )
                    ctx.review = reviewer.process(ctx.report)

                    if ctx.review.approved:
                        progress.update(
                            task,
                            description=f"✅ 评审通过 (评分: {ctx.review.overall_score})",
                        )
                        break

                    progress.update(
                        task,
                        description=f"🔄 评审未通过 (评分: {ctx.review.overall_score})，重新生成...",
                    )

                    if attempt < self.max_review_retries:
                        ctx.report = self.generator.process(
                            generator_input, feedback=ctx.review,
                        )
            except ImportError:
                pass  # Reviewer 未实现时跳过

            # Step 6: Output
            task = progress.add_task("💾 输出报告...", total=None)
            ctx.output_path = self._write_output(ctx, output_path)
            progress.update(task, description=f"✅ 输出完成: {ctx.output_path}")

        # 同步 usage stats
        if isinstance(getattr(self.llm, 'usage_stats', None), UsageStats):
            ctx.usage_stats = self.llm.usage_stats
            if ctx.usage_stats.total_calls > 0:
                self._print_usage_summary(ctx)

        return ctx

    def _print_usage_summary(self, ctx: PipelineContext) -> None:
        """打印模型调用成本摘要."""
        stats = ctx.usage_stats
        table = Table(title="模型调用统计")
        table.add_column("模型", style="cyan")
        table.add_column("调用次数", justify="right")
        table.add_column("Prompt Tokens", justify="right")
        table.add_column("Completion Tokens", justify="right")
        table.add_column("Total Tokens", justify="right", style="bold")

        for usage in stats.by_model.values():
            table.add_row(
                usage.model_name,
                str(usage.call_count),
                f"{usage.prompt_tokens:,}",
                f"{usage.completion_tokens:,}",
                f"{usage.total_tokens:,}",
            )

        table.add_section()
        table.add_row(
            "[bold]合计[/bold]",
            str(stats.total_calls),
            f"{stats.total_prompt_tokens:,}",
            f"{stats.total_completion_tokens:,}",
            f"{stats.total_tokens:,}",
        )

        console.print()
        console.print(table)

    def _write_output(self, ctx: PipelineContext, output_path: str | None) -> str:
        """写入输出文件."""
        if not ctx.report:
            return ""

        if not output_path:
            # 自动生成输出路径
            Path(self.output_dir).mkdir(parents=True, exist_ok=True)
            base_name = Path(ctx.input_files[0]).stem if ctx.input_files else "report"
            ext_map = {"markdown": ".md", "docx": ".docx", "pptx": ".pptx", "pdf": ".pdf"}
            ext = ext_map.get(ctx.output_format, ".md")
            output_path = str(Path(self.output_dir) / f"{base_name}_report{ext}")

        if ctx.output_format == "markdown":
            return write_markdown(ctx.report, output_path)
        elif ctx.output_format == "docx":
            try:
                from src.outputs.docx_writer import write_docx
                return write_docx(ctx.report, output_path)
            except ImportError:
                logger.warning("python-docx not installed, falling back to markdown")
                output_path = output_path.replace(".docx", ".md")
                return write_markdown(ctx.report, output_path)
        elif ctx.output_format == "pptx":
            try:
                from src.outputs.pptx_writer import write_pptx
                return write_pptx(ctx.report, output_path)
            except ImportError:
                logger.warning("python-pptx not installed for output, falling back to markdown")
                output_path = output_path.replace(".pptx", ".md")
                return write_markdown(ctx.report, output_path)
        elif ctx.output_format == "pdf":
            try:
                from src.outputs.pdf_writer import write_pdf
                return write_pdf(ctx.report, output_path)
            except ImportError:
                logger.warning("weasyprint not installed, falling back to markdown")
                output_path = output_path.replace(".pdf", ".md")
                return write_markdown(ctx.report, output_path)
        else:
            return write_markdown(ctx.report, output_path)
