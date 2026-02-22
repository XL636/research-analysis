# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added
- Web: Settings 页 Per-Agent 模型选择 — 5 个 Agent 卡片各带模型下拉框，即时保存到 settings.yaml (T-42)
- Web: 内联 API Key 提示 — 当所选模型缺少 API Key 时，在卡片内直接输入保存 (T-42)
- API: GET/PUT /api/settings/agent-models 端点，支持查询和更新 Agent-模型分配 (T-42)
- Web: Settings 页面 — API Key 管理（GET/PUT /api/settings/api-keys），支持保存到 config/.env + 自动同步 os.environ (T-41)
- Web: i18n 双语支持 zh-CN + en，react-i18next + 语言切换按钮 + localStorage 持久化 (T-40)

### Previously Added
- API: FastAPI backend with CORS, lifespan, health endpoint (T-22)
- API: Knowledge Base endpoints - search, documents, document detail, tags (T-23)
- API: Dashboard stats aggregation endpoint (T-24)
- API: Pipeline endpoints - file upload, SSE progress streaming, results (T-25)
- API: Reports download endpoint (T-25)
- API: PipelineRunner async wrapper with asyncio.Queue progress (T-25)
- API: File upload manager with type validation (T-25)
- CLI: `serve` command to start Web UI server (T-22)
- Web: React + Vite + TypeScript + Tailwind v4 frontend project (T-26)
- Web: Design system - Indigo primary, Emerald accent, Crimson Pro + Atkinson Hyperlegible fonts (T-26)
- Web: TypeScript interfaces mirroring Python Pydantic models (T-26)
- Web: API client layer with axios (pipeline, knowledge, dashboard) (T-26)
- Web: Custom hooks - usePipelineProgress (SSE), useDocuments, useSearch with debounce (T-26)
- Web: Sidebar navigation + AppLayout with React Router (T-27)
- Web: UI component library - KpiCard, Badge, SearchInput, DataTable, FileDropzone, ProgressStepper, MarkdownRenderer, EmptyState (T-28)
- Web: Dashboard page with KPI cards + recent activity table (T-29)
- Web: Knowledge Base page with FTS5 search, tag filter, document table (T-30)
- Web: Document Detail page with analysis cards and SVG relevance score (T-30)
- Web: Analyze page - file upload with format selector and synthesis toggle (T-31)
- Web: Analyze page - SSE progress stepper and report preview/download (T-32)
- Web: Production build (vite build → dist/) + FastAPI static file serving + SPA routing (T-33)
- Core: Pydantic data models for pipeline data flow (T-03)
- Core: Unified LLM client with multi-model support via OpenAI-compatible API (T-04)
- Core: Agent base class with prompt loading and LLM calling (T-05)
- Core: Pipeline engine orchestrating Parse → Analyze → Synthesize → Generate → Review (T-10)
- Parsers: PDF parser using PyMuPDF (T-06), PPT parser using python-pptx (T-13), Note parser for MD/TXT/DOCX (T-14)
- Agents: Parser, Analyzer, Generator, Reviewer, Synthesizer (T-07/T-08/T-09/T-15/T-17)
- Pipeline: Reviewer feedback loop with configurable max retries (T-18)
- Store: SQLite + FTS5 knowledge base with tag system (T-19)
- Outputs: Markdown, DOCX, PPTX report writers (T-20)
- CLI: analyze, search, list commands via Typer (T-11/T-21)
- Config: settings.yaml with per-agent model assignment, 4 prompt templates (T-12/T-21)

- CLI: `batch` command for bulk processing directories with progress bar (T-35)
- CLI: `export` command - export knowledge base to JSON/CSV (T-36)
- CLI: `import` command - import knowledge base from JSON backup (T-36)
- Store: KnowledgeBase.export_json/export_csv/import_json methods (T-36)
- Core: UsageStats model for tracking LLM token usage per model (T-37)
- Core: LLMClient auto-records prompt/completion tokens from API responses (T-37)
- Core: Pipeline prints Rich table cost summary after each run (T-37)
- Docker: Multi-stage Dockerfile (node:22-alpine + python:3.11-slim) (T-38)
- Docker: docker-compose.yml with volume mounts and healthcheck (T-38)
- Docker: .dockerignore for optimized builds (T-38)
- Templates: Meeting report template for seminar presentations (T-39)
- CLI: `--template meeting` option for analyze and batch commands (T-39)

### Testing
- 196 tests total (166 Python + 30 frontend), all passing
- Backend: models, LLM client, engine, parsers, agents, knowledge base, API routes, CLI commands
- Frontend: Badge, KpiCard, SearchInput, EmptyState, ProgressStepper, MarkdownRenderer

## [0.0.1] - 2026-02-21

### Added
- Initial project structure
- Project scaffolding and base configuration
