"""Async Pipeline wrapper with progress reporting."""

from __future__ import annotations

import asyncio
import uuid
from pathlib import Path

from loguru import logger

from src.api.schemas import StepProgress
from src.core.engine import Pipeline


# In-memory store for pipeline runs
_runs: dict[str, dict] = {}


def get_run(run_id: str) -> dict | None:
    return _runs.get(run_id)


def create_run() -> str:
    run_id = str(uuid.uuid4())[:8]
    _runs[run_id] = {
        "status": "created",
        "queue": asyncio.Queue(),
        "result": None,
        "error": None,
    }
    return run_id


async def run_pipeline(
    run_id: str,
    file_paths: list[str],
    output_format: str = "markdown",
    synthesize: bool = False,
) -> None:
    """Run the pipeline in a background thread, pushing progress to a queue."""
    run = _runs.get(run_id)
    if not run:
        return

    run["status"] = "running"
    queue: asyncio.Queue = run["queue"]

    try:
        pipeline = Pipeline()

        # Step 1: Parse
        await queue.put(StepProgress(step="parse", status="running"))
        parsed = await asyncio.to_thread(pipeline.parser.process, file_paths)
        if not parsed:
            await queue.put(StepProgress(step="parse", status="error", message="No documents parsed"))
            run["status"] = "error"
            run["error"] = "No documents parsed"
            await queue.put(StepProgress(step="complete", status="error"))
            return
        await queue.put(StepProgress(step="parse", status="completed", message=f"{len(parsed)} documents"))

        # Step 2: Analyze
        await queue.put(StepProgress(step="analyze", status="running"))
        analyses = []
        stored_doc_ids: list[int] = []
        for doc in parsed:
            analysis = await asyncio.to_thread(pipeline.analyzer.process, doc)
            analyses.append(analysis)
            # Store in knowledge base
            try:
                from src.store.knowledge_base import KnowledgeBase
                kb = KnowledgeBase()
                doc_id = kb.store_analysis(analysis, file_path=doc.file_path, file_type=doc.file_type.value, source_type="user_upload")
                stored_doc_ids.append(doc_id)
            except Exception:
                pass
        await queue.put(StepProgress(step="analyze", status="completed", message=f"{len(analyses)} analyses"))

        # Step 3: Synthesize (optional)
        synthesis = None
        if synthesize and len(analyses) > 1:
            await queue.put(StepProgress(step="synthesize", status="running"))
            try:
                from src.agents.synthesizer import SynthesizerAgent
                synthesizer = SynthesizerAgent(pipeline.llm, pipeline.config_path)
                synthesis = await asyncio.to_thread(synthesizer.process, analyses)
                await queue.put(StepProgress(step="synthesize", status="completed"))
            except Exception as e:
                await queue.put(StepProgress(step="synthesize", status="error", message=str(e)))
        else:
            await queue.put(StepProgress(step="synthesize", status="completed", message="skipped"))

        # Step 4: Generate
        await queue.put(StepProgress(step="generate", status="running"))
        gen_input = synthesis if synthesis else analyses
        report = await asyncio.to_thread(pipeline.generator.process, gen_input)
        await queue.put(StepProgress(step="generate", status="completed"))

        # Step 5: Review
        await queue.put(StepProgress(step="review", status="running"))
        try:
            from src.agents.reviewer import ReviewerAgent
            reviewer = ReviewerAgent(pipeline.llm, pipeline.config_path)
            review = await asyncio.to_thread(reviewer.process, report)
            if not review.approved and pipeline.max_review_retries > 0:
                report = await asyncio.to_thread(pipeline.generator.process, gen_input, review)
            await queue.put(StepProgress(step="review", status="completed", message=f"score: {review.overall_score}"))
        except Exception:
            await queue.put(StepProgress(step="review", status="completed", message="skipped"))

        # Store report_content in knowledge base for each document
        if report and stored_doc_ids:
            try:
                from src.store.knowledge_base import KnowledgeBase
                kb = KnowledgeBase()
                for did in stored_doc_ids:
                    kb.update_report_content(did, report.content)
            except Exception:
                pass

        # Write output
        output_dir = Path("./output")
        output_dir.mkdir(parents=True, exist_ok=True)
        ext_map = {"markdown": ".md", "docx": ".docx", "pptx": ".pptx"}
        ext = ext_map.get(output_format, ".md")
        output_path = str(output_dir / f"report_{run_id}{ext}")

        ctx_data = type("Ctx", (), {
            "report": report,
            "output_format": output_format,
            "input_files": file_paths,
        })()
        actual_path = pipeline._write_output(ctx_data, output_path)

        run["result"] = {
            "report_content": report.content if report else "",
            "report_title": report.title if report else "",
            "output_format": output_format,
            "output_path": actual_path,
        }
        run["status"] = "completed"
        await queue.put(StepProgress(step="complete", status="completed"))

    except Exception as e:
        logger.error(f"Pipeline run {run_id} failed: {e}")
        run["status"] = "error"
        run["error"] = str(e)
        await queue.put(StepProgress(step="error", status="error", message=str(e)))
