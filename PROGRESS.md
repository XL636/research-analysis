# research-analysis — 项目进度

> 本文件仅追踪项目进度，不包含计划（见 TASKS.md）和开发记录（见 devlogs/）。

## 总览

| 指标 | 值 |
|------|-----|
| 当前阶段 | Phase 9 增强 |
| 总任务数 | 78 |
| 已完成 | 78 |
| 进行中 | 0 |
| 完成率 | 100% |

## 当前进行中

> 暂无正在进行的任务。

## 已完成任务（最新在上）

| 日期 | Task | 说明 |
|------|------|------|
| 2026-02-26 | T-76~78 | 阅读助手增强 — 多会话支持 + AI 推荐问题 + SessionSwitcher + SuggestedQuestions |
| 2026-02-26 | T-71~75 | 阅读辅助助手 — ReaderStore + 分页提取 + 10 个 API 端点 + react-pdf 渲染 + AI 问答面板 |
| 2026-02-26 | T-70 | 分析进度全局持久化 — AnalysisContext 全局状态管理 + GlobalProgressBanner 跨页面进度条 |
| 2026-02-26 | T-69 | 异步并行处理多文档 — Engine/Runner 并行化 + 线程安全 + batch 并行 + 进度增强 |
| 2026-02-26 | T-68 | 自定义报告模板系统 — 模板 CRUD + GeneratorAgent 集成 + CLI + 模板管理页 + 分析页选择器 |
| 2026-02-25 | T-67 | 论文类型识别 — paper_type 字段 + 自适应分析维度 + 前端类型 badge + 动态方法论标题 |
| 2026-02-25 | T-66 | Claude Code Skills — 分析论文 Skill + 论文写作 Skill + CLI 基础设施 |
| 2026-02-25 | T-65 | 分析模式功能 — quick/standard/deep/meeting 四种模式，影响分析深度和报告格式 |
| 2026-02-24 | T-64 | 论文写作流程修复 — 调研后按钮消失/LLM 超时卡死/操作失败状态回退 |
| 2026-02-24 | T-63 | 移除元数据记录 + 知识库批量删除 — metadata fallback 移除/DB 清理迁移/前端防御 |
| 2026-02-24 | T-62 | 论文写作 5 项 UX 优化 — source_type/调研保护/全局进度/agent 分组/两级选模型 |
| 2026-02-24 | T-61 | 全自动文献调研 + 深度引用 — ResearchAgent + PaperDownloader + 深度 CitationRef + KB source_type |
| 2026-02-24 | T-60 | CitationAgent 接入外部学术搜索 — Semantic Scholar / OpenAlex / arXiv + Settings UI |
| 2026-02-24 | T-59 | 融入学术写作知识到 Pipeline Prompt — 4 个 prompt 模板增强 |
| 2026-02-24 | T-58 | 侧边栏折叠功能 — 收起为图标模式，localStorage 持久化 |
| 2026-02-23 | T-57 | 论文写作前端页面：PaperListPage + PaperProjectPage + i18n |
| 2026-02-23 | T-48~56 | 论文写作功能：数据模型、4 个 Agent、Pipeline 引擎、LaTeX 输出、CLI、Web API |
| 2026-02-22 | T-47 | PPTX 重写 + PDF 输出 + 上传格式扩展 |
| 2026-02-22 | T-46 | 知识库详情页「完整报告」Tab |
| 2026-02-22 | T-45 | 知识库标题编辑 + 分组（Collections） |
| 2026-02-22 | T-44 | 知识库删除 + 报告下载 + 时区修复 + 重复检测 |
| 2026-02-22 | T-43 | 修复 PPTX 解析错误 + 时区修复 + 相关性评分 Tooltip |
| 2026-02-22 | T-42 | Per-Agent 模型选择 + 内联 API Key 配置 |
| 2026-02-21 | T-41 | Web UI API Key 设置页面 |
| 2026-02-21 | T-40 | Web UI i18n 双语支持（zh-CN + en） |
| 2026-02-21 | T-39 | 会议报告专用模板（--template meeting） |
| 2026-02-21 | T-38 | Docker 容器化（多阶段构建 + docker-compose） |
| 2026-02-21 | T-37 | 模型调用成本统计（UsageStats + Rich 表格） |
| 2026-02-21 | T-36 | 知识库导出/导入（JSON/CSV export + JSON import） |
| 2026-02-21 | T-35 | 批量处理 CLI（batch 命令 + 进度条） |
| 2026-02-21 | T-34 | API pytest + 前端 Vitest 测试 (168 total) |
| 2026-02-21 | T-33 | 生产构建 (vite build) + FastAPI 静态文件服务 |
| 2026-02-21 | T-32 | Analyze 页面 SSE 进度 + 报告预览/下载 |
| 2026-02-21 | T-31 | Analyze 页面上传表单 + 格式选择 + 综合开关 |
| 2026-02-21 | T-30 | Knowledge Base + Document Detail 页面 |
| 2026-02-21 | T-29 | Dashboard 页面（KPI 卡片 + 最近活动） |
| 2026-02-21 | T-28 | UI 组件库（KpiCard, Badge, SearchInput, DataTable, FileDropzone, ProgressStepper, MarkdownRenderer, EmptyState） |
| 2026-02-21 | T-27 | 布局组件（Sidebar + AppLayout）+ React Router |
| 2026-02-21 | T-26 | React/Vite 项目初始化 + Tailwind v4 + 设计系统 |
| 2026-02-21 | T-25 | Pipeline API + SSE + 文件上传 + 报告下载 |
| 2026-02-21 | T-24 | Dashboard API 统计端点 |
| 2026-02-21 | T-23 | Knowledge Base API 端点 |
| 2026-02-21 | T-22 | FastAPI 骨架 + serve 命令 |
| 2026-02-21 | T-21 | Prompt 模板外置 + CLI search/list 命令 |
| 2026-02-21 | T-20 | DOCX/PPTX 输出适配器 |
| 2026-02-21 | T-19 | SQLite + FTS5 知识库 |
| 2026-02-21 | T-18 | Pipeline 评审反馈循环 |
| 2026-02-21 | T-17 | 评审 Agent |
| 2026-02-21 | T-16 | Pipeline 支持 Synthesizer |
| 2026-02-21 | T-15 | 综合 Agent（跨文档对比） |
| 2026-02-21 | T-14 | 笔记解析器（Markdown/TXT/DOCX） |
| 2026-02-21 | T-13 | PPT 解析器（python-pptx） |
| 2026-02-21 | T-12 | 多模型配置（按 Agent 分配模型） |
| 2026-02-21 | T-11 | CLI 入口 + Markdown 输出 |
| 2026-02-21 | T-10 | Pipeline 引擎（串联 Agent 工作流） |
| 2026-02-21 | T-09 | 生成 Agent（Markdown 报告） |
| 2026-02-21 | T-08 | 分析 Agent（深度文档分析） |
| 2026-02-21 | T-07 | 解析 Agent（文件类型调度） |
| 2026-02-21 | T-06 | PDF 解析器（PyMuPDF） |
| 2026-02-21 | T-05 | Agent 基类 |
| 2026-02-21 | T-04 | 统一 LLM 客户端 |
| 2026-02-21 | T-03 | Pydantic 数据模型 |
| 2026-02-21 | T-02 | 生成标准项目文件 |
| 2026-02-21 | T-01 | 项目初始化 |

## 测试覆盖

| 模块 | 测试数 | 状态 |
|------|--------|------|
| Models (Pydantic + UsageStats) | 51 | 全部通过 |
| LLM Client (含 usage tracking) | 23 | 全部通过 |
| Pipeline Engine | 19 | 全部通过 |
| Agents (4个) | 12 | 全部通过 |
| Parsers (PDF/PPT/Note) | 20 | 全部通过 |
| Knowledge Base (含 export/import) | 15 | 全部通过 |
| CLI (batch/export/import) | 12 | 全部通过 |
| API Routes (FastAPI) | 14 | 全部通过 |
| Frontend Components (Vitest) | 30 | 全部通过 |
| **合计** | **196** | **全部通过** |

## 里程碑进度

| 里程碑 | 状态 | 备注 |
|--------|------|------|
| M1: MVP 可用 | 已完成 | PDF → Markdown 报告 |
| M2: 多源综合 | 已完成 | PPT/TXT/DOCX + 跨文档综合 |
| M3: 完整功能 | 已完成 | 评审循环 + 知识库 + DOCX/PPTX 输出 |
| M4: Web UI | 已完成 | FastAPI + React/Vite 仪表盘 |
| M5: 实用功能 + Docker | 已完成 | 批量处理 + 导出导入 + 成本统计 + 会议模板 + Docker |
| M6: 国际化 + 优化 | 已完成 | i18n 双语 + Settings + 知识库增强 + PPTX/PDF 输出 |
| M7: 论文写作 | 已完成 | 4 Agent Pipeline + LaTeX + CLI + Web UI |
| M8: UI/UX 优化 | 已完成 | 侧边栏折叠 + 分析模式 + 模板系统 + 并行处理 + 进度持久化 |
| M9: 阅读辅助助手 | 已完成 | 文档翻页阅读 + PDF 渲染 + AI 页面问答 + 进度持久化 |

## 阻塞项

> 暂无阻塞项。
