# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Security
- API: SPA fallback 路径遍历修复 — resolve() + is_relative_to() 阻止 `/../` 访问 dist 目录外文件
- API: 文件上传路径遍历修复 — Path.name 清理文件名，阻止 `../../` 逃逸上传目录
- API: 文件上传大小限制 — 读取内容后检查 max_upload_size（默认 50MB）
- Docker: 非 root 用户运行 — 添加 appuser + gosu entrypoint，自动修复 volume 权限
- API: CORS 收紧 — allow_methods/allow_headers 从 `*` 改为显式白名单
- Output: PDF 输出 HTML 注入防护 — title/source_files 做 html.escape()
- Git: .gitignore 追加 config/.env、*.key、*.pem、*.p12

### Fixed
- Docker: named volume 权限修复 — entrypoint 启动时 chown volume 目录，解决 appuser 无写权限导致全部功能不可用
- API: 报告下载临时文件泄露 — 生成异常时 shutil.rmtree 清理 tmp_dir
- Backend: 11 处裸 except pass 替换为 logger.debug/warning 记录异常信息
- Web: 调研后确认大纲按钮不可见 — 大纲操作区状态判断增加 'researched' 状态 (T-64)
- Backend: LLM 客户端添加 timeout（300s 请求/10s 连接）— 防止 API 挂起导致操作无限卡住 (T-64)
- Backend: PolishAgent max_tokens 从 4096 提升到 16384 — 整篇论文润色输出不再被截断 (T-64)
- Backend: polish/write_all_sections 失败时回退项目状态 — 不再永远卡在 polishing/writing 中间态 (T-64)
- Backend: ResearchAgent 移除 metadata-only 回退 — 下载失败的论文直接跳过，不再入库 (T-63)
- KB: 自动清理迁移 — 启动时删除所有 file_type='metadata' 的空白记录 (T-63)
- Web: DocumentDetailPage 防御性处理 — metadata_only 文档显示 EmptyState 而非白屏 (T-63)
- Web: AnalysisCards 空数据防御 — 无 key_findings/methodology 时显示摘要文本 (T-63)

### Changed
- Web: 移除一键写作功能，恢复手动确认流程 (T-64)
- Web: 调研完成后显示"前往大纲"引导按钮 + 重新生成大纲按钮 (T-64)
- Web: PaperProjectPage 参考文献统一为可点击链接，移除 metadata-only badge 和提示 (T-63)
- Web: 调研统计文案简化 — "已分析 X 篇 | 跳过 Y 篇" (T-63)
- Backend: ResearchResultResponse schema 移除 metadata_only 字段 (T-63)

### Added
- API: POST /paper/projects/{id}/outline/regenerate — 调研后重新生成大纲 (T-64)
- Web: 调研论文可点击跳转知识库详情 + 无分析论文 amber 色元数据提示 (T-62)
- Web: 重复调研确认对话框 — 已调研项目再次调研前弹出确认，说明追加不覆盖 (T-62)
- Web: PaperOperationContext + GlobalProgressBanner — 跨页面固定顶部进度条，显示操作名称+计时+导航链接 (T-62)
- Web: 设置页 Agent 分两组 — "分析工作流"(5个) + "论文写作工作流"(5个) (T-62)
- Web: AgentModelCard 两级下拉框 — 先选服务商再选模型，切换服务商自动选首个模型 (T-62)
- Backend: pipeline_runner 显式传 source_type="user_upload" (T-62)
- Backend: writer_engine 重复调研合并 doc_ids 而非覆盖 (T-62)
- Web: usePaper.ts 调研成功后同时刷新引用列表 (T-62)
- i18n: zh-CN/en 新增 26 个翻译 key (T-62)
- Paper: 全自动文献调研 ResearchAgent — 搜索→下载→解析→分析→入库，5 阶段全自动 pipeline (T-61)
- Paper: PaperDownloader 论文下载器 — 支持 arXiv PDF、Unpaywall OA、直接 URL 三种来源 (T-61)
- Paper: CitationRef 深度分析字段 — summary/key_findings_text/methodology_text/contributions_text/has_full_analysis (T-61)
- Paper: WriterAgent/OutlineAgent 深度引用 — 有完整分析的引用传递摘要/关键发现/方法给 LLM (T-61)
- Paper: WriterPipeline 新增 research_papers() 步骤 + RESEARCHED 项目状态 (T-61)
- KB: documents 表新增 source_type 列 — user_upload/auto_research/manual_reference 三种来源 (T-61)
- KB: store_metadata_only() 方法 — 仅存元数据记录（下载失败时使用）(T-61)
- KB: get_research_papers() 方法 — 批量获取完整分析数据 (T-61)
- KB: list_documents() 支持 source_type 筛选 (T-61)
- API: POST /paper/projects/{id}/research — 触发自动文献调研 (T-61)
- API: GET /paper/projects/{id}/references — 获取项目所有参考文献 (T-61)
- Web: PaperProjectPage 新增 Research Tab — 文献调研按钮 + 进度显示 + 参考文献列表 (T-61)
- Web: 知识库页面 source_type 筛选 — 全部/用户上传/自动调研/手动参考 (T-61)
- Config: agent_models 新增 research: deepseek-chat (T-61)
- Paper: CitationAgent 接入外部学术搜索 — Semantic Scholar / OpenAlex / arXiv 三源插件式架构，自动补充论文引用 (T-60)
- Core: src/core/search_client.py — SearchProvider ABC + SemanticScholarProvider / OpenAlexProvider / ArxivProvider + SearchManager 聚合去重 (T-60)
- Web: Settings 页学术搜索源管理区块 — SearchProviderCard 组件，启用/禁用开关，API Key 输入 (T-60)
- API: GET/PUT /api/settings/search-providers 端点 — 查询和更新搜索源配置 (T-60)
- Config: settings.yaml 新增 search_providers 配置段（3 个搜索源，独立 timeout/max_results）(T-60)
- Deps: httpx 从 dev 移至主依赖 (T-60)
- Paper: Pipeline Prompt 融入学术写作知识 — citation（关键词维度覆盖+粒度控制+引用质量标准）、outline（叙事三支柱+5 句摘要公式+会议适配表）、writer（章节结构模板+Gopen&Swan 7 原则+词汇规则）、polish（四维评估框架+叙事连贯性检查+预提交清单）(T-59)
- Web: 侧边栏折叠功能 — 点击收起为图标模式(64px)，展开恢复(256px)，动画过渡，localStorage 持久化
- Web: 论文写作页面 — PaperListPage(项目列表/创建) + PaperProjectPage(大纲/写作/导出) + 中英双语 (T-57)
- Paper: 交互式论文写作功能 — 从主题到完整论文的全流程支持 (T-48~56)
- Paper: 4 个新 Agent — OutlineAgent(大纲)、WriterAgent(写作)、CitationAgent(引用)、PolishAgent(润色) (T-49~52)
- Paper: WriterPipeline 状态机引擎 — 创建→大纲→写作→润色→导出，支持跨会话恢复 (T-53)
- Paper: LaTeX 输出适配器 — 生成 .tex + .bib，支持中英文模板 (T-54)
- Paper: PaperDraft → Report 适配器 — 复用已有 Markdown/DOCX/PDF 输出 (T-54)
- CLI: `paper` 子命令组 — new/outline/write/revise/polish/export/list/status (T-55)
- API: Paper Writing REST API — 完整 CRUD + 大纲修改/确认 + 章节写作/修改 + 润色 + 导出 (T-56)
- Config: agent_models 新增 outline/writer/citation/polish 模型配置 (T-55)
- Store: paper_projects SQLite 表，PaperProject JSON 序列化持久化 (T-48)
- Output: PDF 报告输出 — Markdown→HTML→PDF (weasyprint)，A4 学术排版，CJK 字体支持 (T-47)
- Output: PPTX 学术简洁风重写 — 封面页/章节页/内容页，蓝白配色，Bullet 列表，智能分页 (T-47)
- Web: FileDropzone 添加 .docx MIME type 上传支持 (T-47)
- Web: 分析页和详情页格式选择器添加 PDF 选项 (T-47)
- Docker: weasyprint 系统依赖 + CJK 字体 (fonts-noto-cjk) (T-47)
- CLI: analyze/batch 命令 --format 添加 pdf 选项 (T-47)
- API: 报告下载端点支持 PDF 格式 (T-47)
- Web: 知识库详情页「完整报告」Tab — 当存在 report_content 时显示 Tab 切换（分析卡片 / 完整报告）(T-46)
- Store: documents 表新增 report_content 列 + 自动迁移，Pipeline 分析后自动存储完整报告 (T-46)
- API: get_document 返回 report_content，下载端点优先使用存储的原始报告 (T-46)
- Web: 知识库页左侧分组侧栏 — 全部/未分类/自建分组，支持新建/重命名/删除分组 (T-45)
- Web: 文档详情页 inline 标题编辑 — Pencil 图标触发，Enter 保存，Escape 取消 (T-45)
- Web: 文档详情页分组选择器下拉框 — FolderOpen + select 切换分组 (T-45)
- API: PATCH /documents/{id}/title 端点，更新标题 + FTS5 索引重建 (T-45)
- API: Collections CRUD 端点 — GET/POST/PATCH/DELETE /collections (T-45)
- API: PATCH /documents/{id}/collection 端点，移动文档到分组 (T-45)
- Store: collections 表迁移 + documents.collection_id 列 (T-45)
- Store: list_documents 支持 collection_id 和 uncategorized 筛选 (T-45)
- Web: 文档详情页删除按钮 + 确认对话框，删除后跳转知识库列表 (T-44)
- Web: 文档详情页多格式报告下载（Markdown / DOCX / PPTX）(T-44)
- API: DELETE /documents/{id} 端点，级联删除 FTS + 标签关联 (T-44)
- API: GET /documents/{id}/report 端点，复用现有 writer 生成文件下载 (T-44)
- API: GET /documents/check-duplicate 端点，按文件名检测重复 (T-44)
- Web: 分析页重复文件检测弹窗 — 覆盖旧结果 / 保留两份 / 取消提交 (T-44)
- Web: 相关性评分旁添加 HelpCircle tooltip，悬停显示评分说明（中英双语）(T-43)
- Web: Settings 页 Per-Agent 模型选择 — 5 个 Agent 卡片各带模型下拉框，即时保存到 settings.yaml (T-42)
- Web: 内联 API Key 提示 — 当所选模型缺少 API Key 时，在卡片内直接输入保存 (T-42)
- API: GET/PUT /api/settings/agent-models 端点，支持查询和更新 Agent-模型分配 (T-42)
- Web: Settings 页面 — API Key 管理（GET/PUT /api/settings/api-keys），支持保存到 config/.env + 自动同步 os.environ (T-41)
- Web: i18n 双语支持 zh-CN + en，react-i18next + 语言切换按钮 + localStorage 持久化 (T-40)

### Fixed
- API: /api/health 端点移至 SPA catch-all 之前，修复路由被遮蔽返回 HTML 而非 JSON 的问题
- API: 静态文件 dist_dir 路径改为绝对路径，修复工作目录不同时前端 404 问题
- Store: 时区根因修复 — `_beijing_now()` 显式传入时间戳，`_meta` 表一次性迁移旧 UTC 数据 (T-44)
- Parser: PPTX 解析不再因非占位符 shape 抛出 "shape is not a placeholder" 错误 (T-43)
- Store: 知识库日期默认存储北京时间（UTC+8），列表/搜索显示 `YYYY-MM-DD HH:MM` 格式 (T-43)

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
