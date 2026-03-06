# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Fixed
- Reader: 学习指南/FAQ「保存为笔记」不再重新调用 LLM，直接将已有内容格式化保存，防止重复笔记
- Reader: 三种侧重模式（概念/实践/复习）输出差异增强 — 结构化强制指令 + prompt 末尾覆盖 + temperature 调高

### Added
- Reader: 学习指南三种侧重模式（概念理解 / 实践应用 / 复习备考），前端按钮切换，切换后自动重新生成
- Reader: 学习指南 Prompt 增强 — 每个章节包含学习目标、要点、思考题结构化内容
- Reader: 文档采样策略优化 — >20 页文档增加 1/4 和 3/4 采样点，max_chars 提升至 16000
- Reader: OpenAI (gpt-4o, o4-mini) + Claude (claude-sonnet-4-20250514) 模型支持，LLMClient 自动处理 anthropic provider
- Reader: 阅读辅助模型独立配置 — reader/reader_agent/reader_suggestions 三个 slot，设置页新增"阅读辅助"分组
- Reader: AI 回答引用标注 [p.X] 格式，前端可点击蓝色标签跳转到对应页码
- Reader: 文档概览功能（NotebookLM Source Guide 风格）— 摘要、关键主题、目录结构，LLM 自动生成
- Reader: 右侧面板 Tab 模式（对话 | 概览 | 笔记），取代单一聊天面板
- Reader: 笔记系统 — 从 AI 回答保存为笔记、手动添加笔记、页码关联、CRUD
- Reader: 学习辅助工具 — 生成学习指南和 FAQ，支持保存到笔记
- Reader: 文档概览摘要注入到对话上下文，AI 可引用文档全局信息
- Reader: ChatMessage 保存为笔记按钮（hover 显示书签图标）
- Prompts: reader_overview.txt, reader_study_guide.txt, reader_faq.txt 三个新 Prompt 模板
- DB: reader_document_overview 表 + reader_notes 表
- API: 12 个新端点（概览 2 + 笔记 5 + 学习 2 + 模型相关 3）
- i18n: 30+ 个新翻译 key（中英双语）

### Fixed
- API: SPA 根路由修复 — `/{path:path}` 不匹配空路径 `/`，添加显式 `@app.get("/")` 路由返回 index.html

### Changed
- Reader: Prompt 重写 — reader_assistant.txt 增加引用标注规范和诚实边界要求
- Reader: reader_agent.txt 增加推理链和引用标注规范
- LLMClient: chat_json() 对 anthropic provider 自动回退到 prompt 引导 JSON 输出
- LLMClient: 新增 _provider_for() 方法获取模型 provider 名称

### Added
- Testing: PaperDownloader 契约测试 — 17 个 respx 传输层 mock 测试，覆盖 content-type 拒绝、%PDF 魔数验证、超大文件中止、arXiv/Unpaywall 下载、优先级策略
- Testing: 架构守护测试 — 4 个 AST 分析测试，强制保证 _try_download_pdf 使用 PaperDownloader、_fetch_pdf 检查 content-type 和 %PDF 魔数
- Testing: API 集成测试 — 7 个 TestClient 测试，覆盖 /search、/download-pdf、/download-and-analyze 端点
- Testing: 真实 HTTP 冒烟测试 — 5 个 @pytest.mark.smoke 测试（arXiv 下载、Unpaywall OA、PubMed/DOI 拒绝）
- Testing: 新增 respx 依赖 + pytest markers（smoke/e2e）配置

### Fixed
- Paper Search: PDF 下载功能对非 arXiv 来源（PubMed、CrossRef、bioRxiv、OpenAlex 等）无法下载 — 改用 PaperDownloader 支持 arXiv + Unpaywall DOI→OA + 直链三级下载策略，前端传递 doi 启用 Unpaywall 查找

### Added
- Knowledge Base: paper_search 保存论文时自动生成 report_content，详情页显示「完整报告」Tab
- Knowledge Base: 存量论文首次访问时懒生成 report_content 并回写数据库
- Knowledge Base: DocumentDetail API 返回 source_type 字段，前端可区分论文来源
- Knowledge Base: paper_search 仅含摘要的论文，原文 Tab 改名「摘要」并加琥珀色提示条
- Knowledge Base: 完整原文 Tab 默认不渲染内容，点击「加载原文」按钮后显示，支持收起
- i18n: 新增 5 个 detail.* 翻译 key（tabAbstract/abstractOnlyNote/loadOriginal/collapseText/originalNotLoaded）

### Changed
- Paper Search: _analyze_from_metadata() 重构为使用 AnalyzerAgent — 复用 settings.yaml 模型配置 + 分析模式 prompt（quick/standard/deep），支持 paper_type 识别和自适应分析维度
- Paper Search: 移除 ad-hoc JSON schema 模板（_JSON_SCHEMA_TEMPLATE / _SCHEMA_PARAMS / _build_json_schema），-81 行代码

### Fixed
- Smart Search: 中文查询无 LLM 时搜不到论文 — 新增 80+ 学术术语词典 fallback（中文→英文翻译 + 领域检测），无需 LLM 也能正确生成英文关键词
- Smart Search: LLM 排序分数解析崩溃 — `relevance_score` 字段 LLM 可能返回文字描述而非数字，添加安全解析
- Smart Search: 前端超时显示"未找到论文" — Agent 多轮迭代耗时超 120s，降低迭代上限(4→3)和内部超时(100→60s)，前端超时 120→180s
- Smart Search: 评分 badge 颜色阈值修正 — scoreBadgeColor 阈值从 7/4 (0-10 scale) 改为 0.7/0.4 (0-1 scale)，分数显示改为百分比(如 90%)

### Added
- Smart Search: 无 LLM fallback 排序 — 基于关键词匹配的相关性评分，替代全部 0.5 默认分
- Smart Search: 扩展 10 个学科领域映射 — economics/finance/business/management/social_science/psychology/education/law/environmental/engineering

### Fixed
- KnowledgeBase: 消除重复初始化 — 类级 `_initialized_paths` 标志 + double-checked locking，同一 db_path 只执行一次迁移 SQL
- Pipeline: doc_id 穿透 — `_analyze_and_store()` 返回 `(AnalysisResult, doc_id)` 元组，`PipelineContext.doc_ids` 收集，`_pipeline_analyze` 不再需要 FTS 搜索找回 doc_id

### Added
- Paper Search: 分析模式选择 — 搜索结果卡片新增 quick/standard/deep 三档模式 pill 选择器，standard/deep 尝试下载 PDF + Pipeline 完整分析
- Paper Search: PDF 直接下载 — 新增「下载 PDF」按钮，后端 POST /download-pdf 端点返回 FileResponse，前端触发浏览器下载
- Paper Search: _analyze_from_metadata 根据 mode 调整 prompt 详细程度（standard/deep 要求更多维度分析）

### Fixed
- Paper Search: 修复知识库「原文」Tab 不显示 — 所有 kb.store_analysis() 调用补全 parsed_text=req.abstract，原文 Tab 现可正常显示

### Changed
- Paper Search: mode 字段改用 Literal["quick","standard","deep"]，Pydantic 自动拒绝无效值
- Paper Search: 提取 _metadata_analyze_and_store() / _pipeline_analyze() 共享辅助函数，消除 save_to_kb 与 download_and_analyze 逻辑重复
- Paper Search: download-pdf 端点添加 BackgroundTasks 清理临时文件，防止磁盘增长
- Paper Search: downloadPdf 改用 axios + 修复 blob URL 跨浏览器竞态
- Paper Search: 前端 PaperAnalysisMode 类型统一导出，全链路类型一致

### Added
- Paper Search: 论文 AI 对话 — 搜索结果卡片新增"AI 对话"按钮，弹出模态对话框，基于论文元数据 SSE 流式问答
- Paper Search: API POST /api/paper-search/chat — SSE 流式端点，构造论文上下文 system prompt + glm-4-flash 模型
- Knowledge Base: 知识库详情页新增「论文原文」Tab — 当存在 parsed_text 时显示第三个 Tab，展示解析后的完整原文
- Knowledge Base: documents 表新增 parsed_text 列 — Pipeline 分析时自动存储 ParsedDocument.full_text
- i18n: 新增 6 个翻译 key — tabOriginal + 5 个 paperSearch.chat* key (zh-CN + en)

### Fixed
- Paper Search: 修复「分析并存入知识库」不生效 — PDF 下载失败时改用 LLM 从摘要生成结构化 AnalysisResult，不再走 store_metadata_only 空白路径
- Paper Search: save-to-kb 端点同步修复 — 用 _analyze_from_metadata + store_analysis 替代 store_metadata_only

### Tests
- Paper Search: 新增 TestCrossRefProvider 测试类（8 个测试）— 解析、year 边界、错误处理 (T-87)
- Paper Search: 新增 TestCLIResourceCleanup 测试类（2 个测试）— 异常后资源清理 (T-87)
- Paper Search: 修复 provider 注册测试 5→6 个 provider (T-87)
- 全量测试 198 passed (pytest) + 30 passed (vitest)

### Fixed
- Smart Search: 修复评分徽章颜色阈值 — scoreBadgeColor 从 0-10 刻度改为 0-1 刻度，匹配后端 relevance_score 范围
- Smart Search: 修复智能搜索"闪一下就消失"— 前端 providers 字符串→数组 + 后端 validator 兼容双类型 (T-87)
- Smart Search: 修复 Docker 环境 Python 3.11 f-string 反斜杠语法错误导致 500 (T-87)
- Smart Search: 修复前端超时（120s→300s）+ Semantic Scholar 429 熔断机制避免无谓等待 (T-87)
- Web: 论文搜索结果切换页面后不再消失 — 模块级缓存保存搜索状态，Smart Search 数据额外缓存 (T-87)
- Paper Search: SearchResultCard 补全 crossref 来源的颜色和标签映射 (T-87)
- Paper Search: CrossRef 日期解析增加 None/非 int 类型安全检查，防止显示 "None" (T-87)
- Smart Search: Agent 深读 prompt 摘要分隔符添加换行，改善 LLM 边界识别 (T-87)
- CLI: paper-search 和 smart-search 命令用 try/finally 防止 httpx Client 资源泄漏 (T-87)

### Added
- Paper Search: 新增 CrossRef 搜索源 — 完全免费，覆盖有 DOI 的中文期刊论文 (T-87)
- Paper Search: 中文查询自动生成知网/万方/百度学术快捷搜索链接 (T-87)
- Web: 智能搜索结果页新增琥珀色中文数据库链接卡片 (T-87)
- Web: Provider 按钮新增 CrossRef 选项 (T-87)
- CLI: smart-search 中文查询末尾输出数据库链接 (T-87)
- i18n: 新增 CrossRef + 中文数据库相关翻译 key (T-87)
- Smart Search: PaperSearchAgent Agent 化改造 — 自主决策循环（最多 4 轮迭代），自动评估结果质量并决定下一步动作 (T-86)
- Smart Search: 自适应 Provider 选择 — 根据检测到的研究领域（medical/CS/AI 等）自动选择最优搜索源 (T-86)
- Smart Search: 深读迭代 — 读取高分论文摘要提取领域术语，追加搜索发现更多相关论文 (T-86)
- Smart Search: SmartSearchOutput 新增 iterations_used/search_log/domain_detected/quality_score 字段 (T-86)
- API: SmartSearchResponse 新增 4 个可选字段，向后兼容 (T-86)
- Web: 智能搜索意图卡片增加迭代次数、检测领域、质量评分标签 (T-86)
- Web: 多轮搜索时显示搜索日志折叠面板，展示 Agent 决策过程 (T-86)
- CLI: smart-search 输出增加领域检测、迭代轮数、质量评分信息 (T-86)
- i18n: 新增 8 个迭代相关翻译 key (zh-CN + en) (T-86)
- Paper Search: 论文搜索功能 — 支持 PubMed、arXiv、bioRxiv/medRxiv、Semantic Scholar、OpenAlex 五大学术数据库 (T-81~T-84)
- Paper Search: PubMedProvider — NCBI E-utilities API (esearch + efetch) (T-81)
- Paper Search: BiorxivProvider — Europe PMC REST API，同时覆盖 bioRxiv + medRxiv (T-81)
- Paper Search: SearchManager 增强 — 新增 provider_names 参数支持按名称过滤搜索源 (T-81)
- API: GET /api/paper-search/search — 搜索外部学术论文（支持指定搜索源） (T-82)
- API: POST /api/paper-search/save-to-kb — 保存论文元数据到知识库 (T-82)
- API: POST /api/paper-search/download-and-analyze — 下载 PDF 并自动分析入库 (T-82)
- CLI: paper-search 命令 — 支持 --providers/-p、--limit/-n、--save/-s、--json 参数 (T-83)
- Web: PaperSearchPage — 论文搜索页面，搜索框 + 来源过滤器 + 结果数量选择 (T-84)
- Web: SearchResultCard — 搜索结果卡片，来源 Badge（5 种颜色）+ 摘要折叠 + 保存/下载/查看操作 (T-84)
- Web: 侧边栏新增「论文搜索」导航项 (T-84)
- i18n: 论文搜索功能中英文翻译 + PubMed/bioRxiv 设置项翻译 (T-84)
- Reader: Agent 模式 — 可选 Agent 模式，AI 拥有工具调用能力，可自主搜索文档页面、获取指定页内容、查询知识库，多步推理后给出综合回答 (T-80)
- Reader: Agent 工具集 — search_pages/get_page/search_knowledge_base/get_document_info 4 个工具 (T-80)
- Reader: Agent 思考步骤展示 — 流式输出中实时显示工具调用进度（旋转图标 + 结果摘要）(T-80)
- Web: ChatPanel Agent 开关按钮 — 输入框右下角小按钮，一键切换普通/Agent 模式 (T-80)
- API: stream-chat 端点 agent_mode 分支 — Agent 模式走工具循环 + tool_use/tool_result SSE 事件 (T-80)
- Config: reader.agent_model + reader.agent_max_iterations 配置项 (T-80)
- Prompt: reader_agent.txt Agent 模式专用 system prompt (T-80)
- i18n: Agent 模式相关 7 个翻译 key (zh-CN + en) (T-80)
- Reader: AI 回复流式输出 — SSE 逐字显示 + 闪烁光标，无需等待完整生成 (T-79)
- Reader: 智能上下文选页 — 三种策略可配置切换：fixed（固定±N页）、keyword（FTS5全文搜索最相关页）、smart（FTS粗筛+LLM精排）(T-79)
- LLM: stream_chat() 流式聊天方法 — 基于 OpenAI SDK stream=True，逐块 yield 文本片段 (T-79)
- API: POST /reader/{id}/sessions/{sid}/stream-chat — SSE 流式端点，事件格式 delta/done/error (T-79)
- Store: reader_pages_fts FTS5 虚拟表 — contentless 索引，自动回填已有数据 (T-79)
- Store: search_pages() 全文搜索方法 + get_pages_by_nums() 批量取页 (T-79)
- Web: streamSessionChat() — fetch + ReadableStream 解析 SSE POST 响应 (T-79)
- Web: useStreamChat() hook — 管理流式状态（streamingContent/isStreaming/error）(T-79)
- Web: ChatPanel 流式渲染 — 流式文本 + Markdown 渲染 + 闪烁光标▌，等待首字时显示跳动圆点 (T-79)
- Config: context_strategy 配置项（fixed/keyword/smart）+ context_search_limit 参数 (T-79)
- Reader: 多会话支持 — 一个文档可有多个对话，支持切换、新建、删除，首条消息自动生成标题 (T-76~T-78)
- Reader: AI 推荐问题 — 翻页时自动生成 2-3 个基于当前页的问题，可点击芯片直接发送 (T-76~T-78)
- Reader: SessionSwitcher 会话切换下拉菜单 — 嵌入 ChatPanel header，显示标题/消息数/删除 (T-78)
- Reader: SuggestedQuestions 组件 — 无消息时居中大尺寸展示，有消息时输入框上方紧凑 chip 行 (T-78)
- Store: reader_sessions 表 + reader_suggested_questions 表 + reader_chats.session_id 迁移 (T-76)
- API: 7 个新端点 — sessions CRUD + session chat + suggestions（含 LLM 缓存） (T-77)
- Config: reader_suggestions.txt prompt + settings.yaml suggestions_model/count/min_content 配置 (T-77)
- i18n: zh-CN/en 新增 reader.suggestions/newSession/deleteSession 等 7 个翻译 key (T-78)
- Reader: 阅读辅助助手模块 — 上传任意文件，翻页阅读 + AI 实时问答 (T-71~T-75)

### Fixed
- Reader: 修复删除文档失败 — FTS5 索引损坏时自动重建，确保删除不受影响
- Reader: PDF 加载错误提示优化 — 预检文件可达性，404 时提示"文件不存在，请重新上传"
- Reader: 修复 PDF worker 加载 — 改用 Vite ?url 导入模式，解决路径解析不可靠问题
- Reader: 修复 AI 无回复 — glm-4.5-plus 模型不存在，改用 glm-4-plus（1s 响应） (T-78)
- Reader: LLM 调用改用 asyncio.to_thread — 避免阻塞 FastAPI 事件循环导致所有请求排队 (T-77)
- Reader: 发送中禁用推荐问题芯片 — 防止连续点击发送多条消息 (T-78)
- Reader: AI 回复失败时显示红色错误提示 (T-78)
- Reader: ReaderStore SQLite 存储层 — reader_documents/reader_pages/reader_chats 3 张表 (T-71)
- Reader: 文件分页提取服务 — PDF 按自然页、PPTX 按幻灯片、DOCX 按标题、MD/TXT 按段落分页 (T-72)
- Reader: 10 个 API 端点 — upload/list/get/delete/page/file/progress/chat/history/clear (T-73)
- Reader: AI 问答 — 当前页 + 前后各 1 页上下文 + 最近对话历史，调用 GLM-5 模型 (T-73)
- Reader: reader_assistant.txt 阅读辅助 system prompt (T-73)
- Config: settings.yaml 新增 reader 配置段 + agent_models.reader: glm-5 (T-73)
- Web: react-pdf + pdfjs-dist — PDF 浏览器端原生渲染，保留排版/图表/公式 (T-74)
- Web: ReaderListPage 文档列表页 — 卡片网格 + 上传对话框 + 阅读进度条 (T-74)
- Web: ReaderViewPage 核心阅读视图 — 左右分栏布局（62%文档 + 38%对话） (T-75)
- Web: PdfPageViewer — react-pdf 单页渲染（文本层可选中） (T-75)
- Web: TextPageViewer — 非 PDF 文件 MarkdownRenderer 渲染 (T-75)
- Web: PageNavigation — 上/下页 + 页码输入跳转 (T-75)
- Web: ChatPanel + ChatMessage — AI 对话面板，消息标注页码 (T-75)
- Web: 键盘快捷键 ← → 翻页, Escape 收起/展开对话面板 (T-75)
- Web: 翻页自动保存阅读进度 + 预加载前后各 1 页 (T-75)
- Web: Sidebar 新增阅读助手导航项（BookOpenCheck 图标） (T-74)
- i18n: zh-CN/en 新增 reader.* 30+ 翻译 key (T-74)

- Web: 第 5 个"自定义"分析模式 — 自选模板 + 自选深度（quick/standard/deep），原有 4 个模式行为不变 (T-68)
- API: POST /pipeline/run 新增 depth 参数，custom 模式下用 depth 映射 analyzer 配置 (T-68)
- Core: engine.py template_content 优先分支 — 有模板时不传 generator prompt_override，让模板控制报告格式 (T-68)
- Config: 恢复 standard.generator_prompt，使 4 个预设模式各自有完整的 prompt 链 (T-68)
- i18n: zh-CN/en 新增 analyze.customMode/depthLabel/depth.* 等 8 个翻译 key (T-68)
- Core: 自定义报告模板系统 — ReportTemplate 模型 + SQLite 存储 + 内置模板自动同步 + CRUD API (T-68)
- Core: GeneratorAgent 模板优先级链 — prompt_override > template_content > TEMPLATES dict > default (T-68)
- CLI: `template` 子命令组 — list/show/create/delete，`analyze --template-id` 选项 (T-68)
- API: `/api/templates` CRUD 端点 — 列表/详情/创建/更新/删除（内置模板只读） (T-68)
- API: `POST /pipeline/run` 新增 template_id 参数，使用自定义模板分析 (T-68)
- Web: TemplatesPage 模板管理页 — 卡片网格、创建/编辑/预览对话框、内置/自定义标签 (T-68)
- Web: AnalyzePage 模板选择器 — 模式卡片下方可选自定义模板 (T-68)
- Core: 异步并行处理多文档 — Engine/Runner Analyze 步骤并行化，`max_concurrency` 可配置 (T-69)
- Core: UsageStats + LLMClient 线程安全 — threading.Lock 保护共享状态 (T-69)
- Core: pipeline_runner asyncio.gather + Semaphore 并行分析 + 子进度消息 (T-69)
- Core: engine.py ThreadPoolExecutor 并行分析（CLI 路径） (T-69)
- CLI: `batch --concurrency` 选项 — 多文件并行处理 (T-69)
- Web: ProgressStepper 子进度显示 — running 步骤显示 `[1/3] paper.pdf` 等消息 (T-69)
- Config: settings.yaml 新增 max_concurrency/batch_max_concurrency 并发配置 (T-69)
- i18n: zh-CN/en 新增 template.* + analyze.parallel.* 翻译 key (T-68, T-69)
- Web: 分析模式详情提示条 — 选中模式后显示文本上限、评审状态、使用建议，custom 模式根据深度动态显示 (T-68)
- i18n: zh-CN/en 新增 8 个 analyze.modeHint.* 翻译 key (T-68)
- Web: 分析进度全局持久化 — AnalysisContext 全局状态管理 + GlobalProgressBanner 跨页面绿色进度条，跳转页面不丢失进度 (T-70)
- Config: settings.yaml 新增 glm-5 旗舰模型 + glm-4-0414/glm-4-plus-0414/glm-4-air-0414/glm-z1-air-0414 系列模型配置
- Core: 论文类型识别 — AnalysisResult 新增 paper_type 字段（empirical/theoretical/survey/opinion/technical），LLM 自动识别论文类型 (T-67)
- Prompt: 3 个 analyzer prompt（system/deep/quick）加入类型识别步骤，方法论评估改为按类型自适应的论证方式评估 (T-67)
- Skill: analyze-paper Skill 同步更新 — 新增 paper_type 维度，JSON schema 和报告模板自适应 (T-67)
- Web: 文档详情页论文类型 badge — 5 种类型各有独立颜色标识 (T-67)
- Web: 方法论区块标题按 paper_type 动态显示 — 实证→研究方法/理论→论证方式/综述→综合方法/观点→论证结构/技术→技术路线 (T-67)
- i18n: zh-CN/en 新增 12 个论文类型相关翻译 key (T-67)
- Skill: analyze-paper — Claude Code Skill，用 Claude 200K 上下文直接读 PDF 全文进行 8 维深度分析，单次调用替代多步 Agent Pipeline (T-66)
- Skill: write-paper — Claude Code Skill，5 阶段交互式论文写作流程（需求收集→文献检索→大纲生成→逐章写作→润色导出），集成知识库深度引用 (T-66)
- CLI: `store-analysis` 命令 — 将 AnalysisResult JSON 文件存入知识库，供 Skill 调用 (T-66)
- CLI: `get-analysis` 命令 — 获取单篇文档的完整分析 JSON 输出，供 Skill 调用 (T-66)
- CLI: `search --json` 参数 — JSON 格式输出搜索结果，供 Skill 程序化读取 (T-66)
- Core: 分析模式功能 — 4 种预设模式（快速摘要/标准分析/深度研究/会议报告），各自定义 analyzer/generator prompt、文本上限、是否跳过评审 (T-65)
- Config: settings.yaml 新增 analysis_modes 配置区块，支持按模式分发 prompt 和行为参数 (T-65)
- Config: 4 个新 prompt 文件 — analyzer_quick.txt、analyzer_deep.txt、generator_quick.txt、generator_deep.txt (T-65)
- Core: BaseAgent 新增 prompt_override 参数，支持按模式动态切换 system prompt (T-65)
- Core: AnalyzerAgent 新增 max_text_length 参数，替换硬编码 8000 字符上限 (T-65)
- Core: Pipeline 新增 mode 参数，从配置读取模式束分发给各 Agent (T-65)
- CLI: analyze/batch 命令新增 --mode/-m 参数（quick/standard/deep/meeting），优先于 --template (T-65)
- API: GET /pipeline/modes 端点 — 返回可用分析模式列表 (T-65)
- API: POST /pipeline/run 新增 mode 参数 (T-65)
- Web: 分析页新增模式选择器 — 4 个卡片含图标/名称/描述，支持中英双语 (T-65)
- i18n: zh-CN/en 新增 analyze.analysisMode key (T-65)

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
- Web: 移除旧的 standard-only 模板选择器和 modeOverrideHint 提示，模板选择移入"自定义"模式子面板 (T-68)
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
