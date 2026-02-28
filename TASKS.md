# research-analysis — 项目蓝图

> 每完成一个 task 就 git commit + push，形成清晰的开发轨迹。
> Task 编号格式：T-XX，用于在 PROGRESS.md 和 devlog 中引用。

## 项目愿景

构建一个研讨会/组会分析工具，支持从多种研究材料（论文、PPT、录音、笔记）自动生成组会报告和结构化知识库。采用多 Agent 工作流架构，使用国内大模型，按 Agent 分配不同模型以平衡成本和效果。

## 里程碑

| 里程碑 | 目标 | 对应阶段 |
|--------|------|----------|
| M1: MVP 可用 | 输入 PDF → 输出 Markdown 分析报告 | Phase 1 |
| M2: 多源综合 | 多格式输入 + 跨文档综合分析 | Phase 2 |
| M3: 完整功能 | 评审循环 + 知识库 + 多格式输出 | Phase 3 |
| M4: Web UI | FastAPI + React/Vite 仪表盘 | Phase 4 |
| M5: 实用功能 + Docker | 批量处理 + 导出导入 + Docker | Phase 5 |

---

## Phase 0: 项目初始化 `[完成]`

- [x] **T-01: 初始化项目结构**
  - 目标：搭建可运行的项目骨架
  - 步骤：① uv init → ② 安装核心依赖 → ③ 创建目录结构
  - 验收：`uv sync` 成功，所有目录就绪
  - 依赖：无

- [x] **T-02: 生成标准项目文件**
  - 目标：README、CLAUDE.md、TASKS.md 等基础文件就绪
  - 步骤：① 运行 project-init → ② 配置 settings.yaml → ③ 创建 .env.example
  - 验收：所有标准文件存在且内容正确
  - 依赖：T-01

## Phase 1: 基础骨架 + MVP `[完成]`

- [x] **T-03: 创建 Pydantic 数据模型**
  - 目标：定义 Agent 间传递的数据结构
  - 步骤：① ParsedDocument → ② AnalysisResult → ③ SynthesisResult → ④ Report → ⑤ ReviewFeedback
  - 验收：所有模型可实例化，字段类型正确
  - 依赖：T-01

- [x] **T-04: 构建统一 LLM 客户端**
  - 目标：封装多模型调用，通过 OpenAI 兼容接口统一访问
  - 步骤：① 读取 settings.yaml 配置 → ② 懒加载 OpenAI 客户端 → ③ chat() 和 chat_json() 方法
  - 验收：Mock 测试验证 base_url 正确，消息格式正确
  - 依赖：T-01

- [x] **T-05: 创建 Agent 基类**
  - 目标：提供 LLM 调用、消息构建、Prompt 加载能力
  - 步骤：① BaseAgent 类 → ② process() 抽象方法 → ③ Prompt 模板加载
  - 验收：基类可被继承，提供完整的 LLM 交互能力
  - 依赖：T-04

- [x] **T-06: 实现 PDF 解析器**
  - 目标：从 PDF 提取结构化文本
  - 步骤：① PyMuPDF 读取 → ② 提取标题/段落/图表描述 → ③ 返回 ParsedDocument
  - 验收：真实 PDF 能正确解析为 ParsedDocument
  - 依赖：T-03

- [x] **T-07: 实现解析 Agent**
  - 目标：调度解析器，对提取文本做初步结构化
  - 步骤：① 根据文件类型选择解析器 → ② 调用解析器 → ③ 返回 ParsedDocument
  - 验收：输入文件路径，输出正确的 ParsedDocument
  - 依赖：T-05, T-06

- [x] **T-08: 实现分析 Agent**
  - 目标：对单篇文档进行深度分析
  - 步骤：① 构建分析 Prompt → ② 调用 LLM → ③ 解析为 AnalysisResult
  - 验收：输入 ParsedDocument，输出包含摘要、关键发现、方法论评估的 AnalysisResult
  - 依赖：T-05, T-03

- [x] **T-09: 实现生成 Agent**
  - 目标：按模板生成 Markdown 报告
  - 步骤：① 构建生成 Prompt → ② 调用 LLM → ③ 返回 Report
  - 验收：输入 AnalysisResult，输出格式良好的 Markdown 报告
  - 依赖：T-05, T-03

- [x] **T-10: 构建 Pipeline 引擎**
  - 目标：串联 Parse → Analyze → Generate 工作流
  - 步骤：① 加载配置 → ② 按顺序执行 Agent → ③ rich 进度条显示
  - 验收：输入文件路径，自动走完 Pipeline 输出报告
  - 依赖：T-07, T-08, T-09

- [x] **T-11: 创建 CLI 入口和 Markdown 输出**
  - 目标：`python main.py analyze paper.pdf` 可用
  - 步骤：① typer CLI 框架 → ② analyze 命令 → ③ Markdown 文件输出
  - 验收：命令行输入 PDF 文件，输出 Markdown 报告文件
  - 依赖：T-10

## Phase 2: 多模型 + 更多解析器 + 综合分析 `[完成]`

- [x] **T-12: 完善多模型配置**
  - 目标：不同 Agent 使用不同模型
  - 步骤：① settings.yaml 多模型配置 → ② Agent 自动按配置选模型 → ③ 日志记录模型选择
  - 验收：日志确认不同 Agent 调用了不同模型
  - 依赖：T-10

- [x] **T-13: 实现 PPT 解析器**
  - 目标：从 .pptx 文件提取内容
  - 步骤：① python-pptx 读取 → ② 提取幻灯片文本/图表 → ③ 返回 ParsedDocument
  - 验收：真实 .pptx 能正确解析
  - 依赖：T-03

- [x] **T-14: 实现笔记解析器**
  - 目标：解析 Markdown/TXT/DOCX 笔记
  - 步骤：① 按格式分发 → ② 提取结构化内容 → ③ 返回 ParsedDocument
  - 验收：Markdown/TXT 文件能正确解析
  - 依赖：T-03

- [x] **T-15: 实现综合 Agent**
  - 目标：跨文档对比和主题归纳
  - 步骤：① 多文档输入 → ② 交叉对比 Prompt → ③ 返回 SynthesisResult
  - 验收：输入多个 AnalysisResult，输出跨文档综合分析
  - 依赖：T-05, T-03

- [x] **T-16: 更新 Pipeline 支持 Synthesizer**
  - 目标：多文档时自动启用综合分析
  - 步骤：① 检测多文档输入 → ② 插入 Synthesizer 步骤 → ③ Generator 使用 SynthesisResult
  - 验收：多文件输入产出包含跨文档对比的报告
  - 依赖：T-15, T-10

## Phase 3: 评审 + 知识库 + 多格式输出 `[完成]`

- [x] **T-17: 实现评审 Agent**
  - 目标：对生成报告做质量检查
  - 步骤：① 评审 Prompt → ② 打分 + 反馈 → ③ 返回 ReviewFeedback
  - 验收：能识别报告质量问题并给出具体反馈
  - 依赖：T-05, T-03

- [x] **T-18: Pipeline 加入评审反馈循环**
  - 目标：不合格报告打回重做（最多 2 次）
  - 步骤：① Reviewer 评审 → ② 不合格传反馈给 Generator → ③ 重新生成
  - 验收：Mock Reviewer 拒绝 → Generator 收到反馈 → 重新生成
  - 依赖：T-17, T-10

- [x] **T-19: 实现 SQLite 知识库**
  - 目标：存储分析结果，支持全文搜索
  - 步骤：① SQLite + FTS5 表结构 → ② 存储/查询接口 → ③ 标签系统
  - 验收：存储 → 搜索 → 验证 FTS5 结果正确
  - 依赖：T-03

- [x] **T-20: 实现 DOCX/PPTX 输出**
  - 目标：支持 Word 和 PPT 格式输出
  - 步骤：① docx_writer → ② pptx_writer → ③ CLI 增加 --format 选项
  - 验收：输出的 DOCX/PPTX 文件可正常打开
  - 依赖：T-10

- [x] **T-21: Prompt 模板外置 + CLI 扩展**
  - 目标：Prompt 可配置，CLI 增加 search/list 命令
  - 步骤：① Prompt 移至 config/prompts/ → ② search 命令 → ③ list 命令
  - 验收：修改 Prompt 文件无需改代码；search/list 命令可用
  - 依赖：T-19

## Phase 4: Web UI `[完成]`

### Backend API (FastAPI)

- [x] **T-22: FastAPI 骨架 + pyproject.toml + serve 命令**
  - 目标：创建 FastAPI 应用骨架，添加 web 依赖，CLI serve 命令
  - 依赖：T-21

- [x] **T-23: Knowledge Base API 端点**
  - 目标：文档列表、搜索、标签、文档详情 API
  - 依赖：T-22

- [x] **T-24: Dashboard API 统计端点**
  - 目标：仪表板统计数据 API
  - 依赖：T-22

- [x] **T-25: Pipeline API + SSE + 文件上传 + 报告**
  - 目标：文件上传、Pipeline 运行、SSE 进度推送、报告下载
  - 依赖：T-22

### Frontend (React + Vite + Tailwind)

- [x] **T-26: React/Vite 项目初始化 + Tailwind + 设计系统**
  - 目标：创建 web/ 目录，配置 Vite + React + TypeScript + Tailwind v4
  - 步骤：① package.json → ② Vite/TS 配置 → ③ Tailwind 主题 → ④ 类型定义 → ⑤ API 客户端
  - 依赖：T-22

- [x] **T-27: 布局组件 + React Router**
  - 目标：Sidebar 导航 + AppLayout 布局 + 路由配置
  - 依赖：T-26

- [x] **T-28: UI 组件库**
  - 目标：KpiCard、Badge、SearchInput、DataTable、FileDropzone、ProgressStepper、MarkdownRenderer、EmptyState
  - 依赖：T-26

- [x] **T-29: Dashboard 页面**
  - 目标：仪表板页面，展示统计数据和最近文档
  - 依赖：T-28, T-24

- [x] **T-30: Knowledge Base + Document Detail 页面**
  - 目标：知识库列表页 + 文档详情页
  - 依赖：T-28, T-23

- [x] **T-31: Analyze 页面 - 上传表单**
  - 目标：文件上传表单和格式选择
  - 依赖：T-28, T-25

- [x] **T-32: Analyze 页面 - SSE 进度 + 报告预览**
  - 目标：实时进度显示和报告 Markdown 预览
  - 依赖：T-31

- [x] **T-33: 生产构建 + 静态文件服务**
  - 目标：Vite 构建 + FastAPI 静态文件服务
  - 依赖：T-32

- [x] **T-34: 测试 - API pytest + 前端 Vitest**
  - 目标：后端 API 测试 + 前端组件测试
  - 依赖：T-33

## Phase 5: 实用功能 + Docker 容器化 `[完成]`

- [x] **T-35: 批量处理 CLI**
  - 目标：`python main.py batch ./papers/` 批量分析目录下所有文档
  - 步骤：① 扫描支持的文件格式 → ② Rich 进度条 → ③ --recursive/--output-dir/--synthesize
  - 验收：批量处理多文件，输出汇总表格
  - 依赖：T-11

- [x] **T-36: 知识库导出/导入**
  - 目标：支持 JSON/CSV 导出和 JSON 导入
  - 步骤：① export_json/export_csv 方法 → ② import_json 方法 → ③ CLI export/import 命令
  - 验收：导出 → 导入 → 数据一致
  - 依赖：T-19

- [x] **T-37: 模型调用成本统计**
  - 目标：记录和展示 LLM 调用的 token 用量
  - 步骤：① UsageStats 模型 → ② LLMClient 记录 token → ③ Pipeline 打印 Rich 表格
  - 验收：Pipeline 运行结束后显示按模型分组的 token 统计
  - 依赖：T-04, T-10

- [x] **T-38: Docker 容器化**
  - 目标：一键 Docker 部署
  - 步骤：① 多阶段 Dockerfile → ② docker-compose.yml → ③ .dockerignore
  - 验收：`docker compose up` 启动成功，healthcheck 通过
  - 依赖：T-33

- [x] **T-39: 会议报告专用模板**
  - 目标：组会场景专用报告模板
  - 步骤：① meeting_report.txt 模板 → ② GeneratorAgent 模板选择 → ③ CLI --template 选项
  - 验收：`python main.py analyze paper.pdf --template meeting` 输出组会格式报告
  - 依赖：T-09

## Phase 6: 国际化 + 优化 `[完成]`

- [x] **T-40: Web UI i18n 双语支持（zh-CN + en）**
  - 目标：Web UI 支持中英双语切换
  - 步骤：① react-i18next + i18next 基础设施 → ② 翻译文件 zh-CN.json + en.json → ③ 所有组件/页面 t() 替换 → ④ Sidebar 语言切换按钮
  - 验收：默认中文，可切换英文，刷新保持语言偏好
  - 依赖：T-34

- [x] **T-41: Web UI API Key 设置页面**
  - 目标：在 Web UI 中添加设置页面，让用户直接输入和管理 LLM API Key
  - 步骤：① 后端 schemas + LLMClient.clear_clients() → ② 后端 settings 路由 (GET/PUT /api/settings/api-keys) → ③ 前端类型 + API 层 → ④ i18n + Badge 扩展 → ⑤ SettingsPage + 路由 + 侧边栏导航
  - 验收：Settings 页显示 3 个 provider，输入 Key 保存后状态变为"已配置"，重启后 Key 仍在
  - 依赖：T-40

- [x] **T-42: Per-Agent 模型选择 + 内联 API Key 配置**
  - 目标：Settings 页支持为每个 Agent 选择模型，缺少 API Key 时内联提示输入
  - 步骤：① 后端 schemas (ModelInfo, AgentModelAssignment 等) → ② 后端 GET/PUT /api/settings/agent-models 端点 → ③ 前端类型 + API 层 → ④ AgentModelCard 组件 → ⑤ SettingsPage 重构（Agent 模型卡片 + 可折叠 API Key 表格）→ ⑥ i18n 双语
  - 验收：5 个 Agent 卡片显示模型下拉框，切换模型即时保存到 settings.yaml，缺少 Key 时内联输入并保存
  - 依赖：T-41

- [x] **T-43: 修复 PPTX 解析错误 + 时区修复 + 相关性评分 Tooltip**
  - 目标：修复三个 bug/改进
  - 步骤：① PPT 解析器 try-except 修复非占位符 shape 报错 → ② SQLite 默认时间改为北京时区 + strftime 格式化 → ③ 相关性评分添加 HelpCircle tooltip + i18n
  - 验收：PPTX 含非占位符 shape 不报错，新记录显示北京时间，tooltip 悬停显示评分说明
  - 依赖：T-13, T-19, T-30

- [x] **T-44: 知识库删除 + 报告下载 + 时区修复 + 重复检测**
  - 目标：① 知识库删除功能 ② 分析结果多格式下载 ③ 时区根因修复 ④ 重复提交检测弹窗
  - 步骤：① _beijing_now() + _meta 迁移表修复时区 → ② delete_document + DELETE 端点 + 前端删除按钮/确认框 → ③ _analysis_to_report + GET report 端点 + 前端下载按钮组 → ④ find_by_filename + check-duplicate 端点 + 前端弹窗（覆盖/保留/取消）
  - 验收：删除文档后跳转列表，多格式下载正常，旧数据时区迁移，重复检测弹窗三选项可用
  - 依赖：T-43

- [x] **T-45: 知识库标题编辑 + 分组（Collections）**
  - 目标：① 标题可编辑 ② 分组功能（类似文件夹）
  - 步骤：① 后端 update_title + FTS5 索引重建 → ② collections 表迁移 + 分组 CRUD → ③ list_documents 扩展（collection_id/uncategorized） → ④ 前端详情页 inline 标题编辑 + 分组选择器 → ⑤ 知识库页左侧分组侧栏（新建/重命名/删除/筛选）→ ⑥ i18n
  - 验收：标题编辑保存后列表/搜索可见，分组 CRUD 正常，文档可分组筛选
  - 依赖：T-44

- [x] **T-46: 知识库详情页「完整报告」Tab**
  - 目标：将 Pipeline 生成的散文式报告存入数据库，详情页添加 Tab 切换（分析卡片 / 完整报告）
  - 步骤：① DB 迁移 report_content 列 → ② update/get_report_content 方法 → ③ Pipeline 存储报告 → ④ API + Schema 支持 → ⑤ 前端 Tab UI + MarkdownRenderer → ⑥ 下载优先使用存储的报告 → ⑦ i18n
  - 验收：新分析文档详情页出现两个 Tab，旧文档无 Tab 向后兼容，下载使用存储报告
  - 依赖：T-45

- [x] **T-47: PPTX 重写 + PDF 输出 + 上传格式扩展**
  - 目标：① PPTX 学术简洁风重写 ② 新增 PDF 输出（weasyprint） ③ 前端 .docx 上传支持
  - 步骤：① pptx_writer.py 全部重写（封面页/章节页/内容页，蓝白配色，智能拆分） → ② 新建 pdf_writer.py（Markdown→HTML→PDF，A4 学术排版） → ③ pyproject.toml + Dockerfile 添加 pdf 依赖 → ④ engine/API/CLI 全链路接入 pdf 格式 → ⑤ 前端 FileDropzone 添加 .docx MIME → ⑥ 前端格式选择器添加 PDF → ⑦ i18n 更新
  - 验收：PPTX 蓝白配色有 bullet 列表，PDF A4 中文正常，前端支持 .docx 上传和 PDF 下载
  - 依赖：T-46

## Phase 7: 论文写作功能 `[完成]`

- [x] **T-48: 论文数据模型 + 持久化**
  - 目标：PaperProject, PaperOutline, PaperSection, PaperDraft, CitationRef 模型 + SQLite 存储
  - 步骤：① paper_models.py 数据模型 → ② paper_store.py SQLite 持久化
  - 验收：模型创建/序列化/反序列化正常，CRUD 操作通过
  - 依赖：无

- [x] **T-49: OutlineAgent + outline_system.txt**
  - 目标：大纲生成/修改 Agent
  - 步骤：① outline_system.txt prompt → ② OutlineAgent process/revise 方法
  - 验收：生成结构合理的论文大纲 JSON
  - 依赖：T-48

- [x] **T-50: WriterAgent + writer_system.txt**
  - 目标：逐章节写作/修改 Agent
  - 步骤：① writer_system.txt prompt → ② WriterAgent process/revise 方法
  - 验收：按大纲要点生成章节内容
  - 依赖：T-48

- [x] **T-51: CitationAgent + citation_system.txt**
  - 目标：从知识库收集引用 Agent
  - 步骤：① citation_system.txt prompt → ② CitationAgent 知识库搜索 + LLM 关键词推荐
  - 验收：从知识库加载文献 + 搜索补充引用
  - 依赖：T-48

- [x] **T-52: PolishAgent + polish_system.txt**
  - 目标：全文润色 Agent
  - 步骤：① polish_system.txt prompt → ② PolishAgent 全文润色
  - 验收：润色后论文语言质量、术语统一性提升
  - 依赖：T-48

- [x] **T-53: WriterPipeline 引擎**
  - 目标：交互式状态机引擎，每步暂停等待用户
  - 步骤：① 初始化 4 个 Agent → ② create/outline/write/revise/polish/export 步骤方法 → ③ PaperStore 持久化
  - 验收：完整 Pipeline 可逐步执行，跨会话恢复
  - 依赖：T-49, T-50, T-51, T-52

- [x] **T-54: LaTeX 输出 + 论文适配器**
  - 目标：LaTeX 导出（.tex + .bib）+ PaperDraft → Report 适配
  - 步骤：① latex_writer.py（Markdown→LaTeX, BibTeX） → ② paper_adapters.py（复用 docx/pdf writer）
  - 验收：生成可编译的 LaTeX 文件
  - 依赖：T-48

- [x] **T-55: CLI 集成 + settings.yaml 更新**
  - 目标：main.py paper 子命令组 + 模型配置
  - 步骤：① paper_app Typer 子命令 → ② 8 个命令实现 → ③ settings.yaml 新增 agent_models + paper 配置
  - 验收：`paper new/outline/write/revise/polish/export/list/status` 全部可用
  - 依赖：T-53, T-54

- [x] **T-56: Web API routes + schemas**
  - 目标：paper API 路由 + Pydantic schema + app.py 注册
  - 步骤：① schemas.py 新增 Paper schema → ② routes/paper.py 全部端点 → ③ app.py 注册 paper_router
  - 验收：API /docs 中 Paper 路由可调用
  - 依赖：T-53, T-54

- [x] **T-57: 前端页面（PaperListPage + PaperProjectPage）**
  - 目标：论文写作 Web UI
  - 步骤：① PaperListPage 列表 → ② PaperProjectPage 详情（大纲/写作/导出） → ③ 路由 + 侧边栏
  - 验收：前端可创建项目、查看大纲、触发写作、导出
  - 依赖：T-56

## Phase 8: UI/UX 优化 `[进行中]`

- [x] **T-65: 分析模式功能（quick/standard/deep/meeting）**
  - 目标：用户可选择不同分析模式，影响分析深度和报告格式
  - 步骤：① settings.yaml analysis_modes 配置 → ② 4 个新 prompt 文件 → ③ BaseAgent prompt_override + AnalyzerAgent max_text_length → ④ Pipeline mode 参数 + skip_review → ⑤ CLI --mode 参数 → ⑥ API /pipeline/modes + mode 参数 → ⑦ 前端模式选择器卡片 + i18n
  - 验收：CLI --mode quick/deep/meeting 各走对应 prompt，Web 4 个模式卡片可选，--template 向后兼容
  - 依赖：T-39

- [x] **T-66: Claude Code Skills — 分析论文 + 论文写作**
  - 目标：新增两个 Claude Code Skill，让用户可以用 Claude 直接分析论文/写论文，作为现有 Pipeline 的高质量替代路径
  - 步骤：① main.py 新增 store-analysis/get-analysis 命令 + search --json 增强 → ② analyze-paper Skill（8 维深度分析 + 知识库存储 + Markdown 报告） → ③ write-paper Skill（5 阶段交互式流程：需求→文献→大纲→写作→导出）
  - 验收：Claude Code 中说"分析论文"或"写论文"触发对应 Skill，分析结果存入知识库，论文写作集成知识库引用
  - 依赖：T-19, T-55

- [x] **T-67: 论文类型识别 — 让分析维度自适应论文类型**
  - 目标：识别论文类型（实证/理论/综述/观点/技术），根据类型调整分析维度
  - 步骤：① AnalysisResult 加 paper_type 字段 → ② 3 个 analyzer prompt 加类型识别 + 自适应分析 → ③ Skill 同步更新 → ④ 前端展示类型 badge + 动态方法论标题 → ⑤ i18n 双语
  - 验收：不同类型论文识别正确，前端标题和 badge 自适应，旧数据向后兼容
  - 依赖：T-65, T-66

- [x] **T-58: 侧边栏折叠功能**
  - 目标：侧边栏支持折叠/展开，收起后仅显示图标
  - 步骤：① Sidebar 组件添加 collapsed 状态 → ② 收起模式仅显示图标 + hover tooltip → ③ AppLayout main 区域动态调整 margin → ④ localStorage 持久化折叠状态
  - 验收：点击折叠按钮侧边栏收起为 64px 图标模式，展开恢复 256px，刷新后保持状态
  - 依赖：T-27

- [x] **T-59: 融入学术写作知识到 Pipeline Prompt**
  - 目标：将 ml-paper-writing skill 中的关键知识精炼后融入 4 个 prompt 模板
  - 步骤：① citation_system.txt 关键词维度覆盖+粒度控制+引用质量标准 → ② outline_system.txt 叙事三支柱+5 句摘要公式+会议适配表 → ③ writer_system.txt 章节结构模板+7 原则+词汇规则 → ④ polish_system.txt 四维评估+叙事连贯性检查+预提交清单
  - 验收：4 个 prompt 文件更新，JSON schema 与 Agent 代码完全匹配，不改任何 Python 代码
  - 依赖：T-49, T-50, T-51, T-52

- [x] **T-60: CitationAgent 接入外部学术文献搜索**
  - 目标：插件式接入 Semantic Scholar / OpenAlex / arXiv 外部学术搜索 API，补充论文引用
  - 步骤：① settings.yaml 新增 search_providers 配置 → ② pyproject.toml httpx 移至主依赖 → ③ src/core/search_client.py（Provider ABC + 3 实现 + SearchManager） → ④ CitationAgent 新增 _search_external() → ⑤ API schemas + GET/PUT /search-providers 端点 → ⑥ 前端 SearchProviderCard 组件 + SettingsPage 搜索源区块 + i18n
  - 验收：Settings 页显示 3 个搜索源卡片，可切换启用/禁用，论文写作 Pipeline 自动从外部 API 补充引用
  - 依赖：T-51

- [x] **T-61: 全自动文献调研 + 深度引用**
  - 目标：新建 ResearchAgent 实现全自动文献调研（搜索→下载→解析→分析→入库），WriterAgent 基于知识库完整分析结果深度引用
  - 步骤：① KB 迁移 source_type 字段 → ② PaperDownloader（arXiv/Unpaywall/直接URL） → ③ ResearchAgent（5阶段流程：关键词→搜索→筛选→下载分析→入库） → ④ CitationRef 新增深度分析字段 → ⑤ CitationAgent 加载完整 AnalysisResult → ⑥ WriterAgent/OutlineAgent 使用丰富引用 → ⑦ WriterPipeline 新增 research_papers 步骤 → ⑧ API 端点（research/references） → ⑨ 前端 Research Tab + KB source_type 筛选
  - 验收：创建论文项目→自动调研→KB 中有 auto_research 文献→写作引用具体发现→KB 页按来源筛选
  - 依赖：T-60

- [x] **T-62: 论文写作 5 项 UX 优化**
  - 目标：修复 source_type 显式声明、调研论文可点击、重复调研保护、全局持久进度条、设置页 agent 分组、两级模型选择
  - 步骤：① pipeline_runner 显式传 source_type → ② 调研论文 Link + 元数据提示 → ③ writer_engine 合并 doc_ids → ④ 重复调研确认对话框 + invalidate references → ⑤ PaperOperationContext + GlobalProgressBanner → ⑥ 设置页分"分析/论文写作"两组 → ⑦ AgentModelCard 两级下拉框 → ⑧ i18n 26 个新 key
  - 验收：调研论文可跳转详情，连续调研不覆盖，全局进度 banner 跨页可见，设置页分组清晰，模型两级联动
  - 依赖：T-61

- [x] **T-63: 移除元数据记录 + 知识库批量删除**
  - 目标：① 知识库批量删除功能 ② 移除 metadata-only 回退，下载失败直接跳过不入库 ③ 清理已有 metadata 记录
  - 步骤：① ResearchAgent 移除 metadata fallback → ② KB 添加清理迁移 → ③ writer_engine/schemas 清理 → ④ 前端防御性处理 + 移除 metadata UI → ⑤ i18n 更新统计文案
  - 验收：下载失败论文不入库，旧 metadata 记录自动清理，DocumentDetailPage 不白屏
  - 依赖：T-61

- [x] **T-64: 论文写作流程修复 — 调研后按钮消失 + LLM 超时卡死**
  - 目标：① 修复调研后确认大纲按钮不可见 ② 修复 LLM 调用无超时导致润色/写作卡死 ③ 操作失败时状态回退
  - 步骤：① 大纲操作区状态判断增加 'researched' → ② 移除一键写作，恢复手动确认 → ③ 调研完成引导按钮 + 重新生成大纲 → ④ OpenAI 客户端添加 timeout → ⑤ PolishAgent max_tokens 提升到 16384 → ⑥ polish/write_all_sections 异常时回退状态
  - 验收：调研后确认按钮可见，润色不再无限卡住，操作失败后项目状态可恢复
  - 依赖：T-62

- [x] **T-68: 自定义报告模板系统**
  - 目标：模板 CRUD + GeneratorAgent 集成 + CLI + 模板管理页 + 分析页选择器
  - 步骤：① ReportTemplate 数据模型 → ② template_store.py SQLite 存储 + 内置模板同步 → ③ GeneratorAgent template_content 优先级链 → ④ Engine/Runner 透传 → ⑤ API CRUD 端点 → ⑥ CLI template 子命令组 + --template-id → ⑦ 前端 TemplatesPage + AnalyzePage 模板选择器 → ⑧ i18n
  - 验收：CLI `template list` 显示内置模板，Web `/templates` CRUD 正常，分析页可选模板
  - 依赖：T-09, T-65

- [x] **T-69: 异步并行处理多文档**
  - 目标：Engine/Runner 并行化 + 线程安全 + batch 并行 + 进度增强
  - 步骤：① settings.yaml max_concurrency 配置 → ② UsageStats/LLMClient 线程安全 → ③ pipeline_runner asyncio.gather + Semaphore → ④ engine.py ThreadPoolExecutor → ⑤ batch 命令 --concurrency 并行 → ⑥ 前端进度 message 子进度显示
  - 验收：多文档分析并行执行，单文档退化为同步，batch --concurrency 可用，进度显示子状态
  - 依赖：T-10, T-35

- [x] **T-70: 分析进度全局持久化**
  - 目标：分析进度跨页面持久化，跳转页面不丢失进度，顶部绿色进度条可随时返回
  - 步骤：① AnalysisContext 全局状态管理 → ② GlobalProgressBanner 顶部进度条 → ③ 跨页面持久化分析状态
  - 验收：开始分析后跳转其他页面，顶部显示绿色进度条，点击可返回分析页，进度不丢失
  - 依赖：T-32

## Phase 9: 阅读辅助助手 `[完成]`

### 阅读助手增强

- [x] **T-79: 流式输出 + 智能上下文**
  - 目标：AI 回复逐字流式显示 + 按问题动态选页（FTS keyword/LLM smart/fixed 三策略）
  - 步骤：① LLMClient stream_chat() → ② SSE 端点 + _prepare_chat_context 重构 → ③ FTS5 索引 + search_pages → ④ 智能选页策略路由 → ⑤ 前端 streamSessionChat API → ⑥ useStreamChat hook → ⑦ ChatPanel 流式渲染 → ⑧ config context_strategy
  - 验收：文字逐字显示 + 闪烁光标，keyword 策略可引用远处页面，旧端点兼容
  - 依赖：T-76~78

- [x] **T-80: 阅读助手 Agent 模式**
  - 目标：新增可选 Agent 模式，LLM 拥有工具调用能力，可自主搜索文档页面、获取页面内容、查询知识库
  - 步骤：① Schema agent_mode 字段 → ② 4 个 Agent 工具定义 + 执行分派 → ③ Agent 流式循环（工具调用→最终流式输出）→ ④ Agent 专用 prompt → ⑤ 前端 SSE tool_use/tool_result 事件 → ⑥ useStreamChat agentSteps 状态 → ⑦ ChatPanel Agent 开关 + 思考步骤展示 → ⑧ i18n
  - 验收：普通模式无回归，Agent 模式可自主搜索多页面再综合回答，思考步骤正确显示
  - 依赖：T-79

- [x] **T-76: 数据库 + Store 层改造（多会话 + 推荐问题）**
  - 目标：新增 reader_sessions/reader_suggested_questions 表，reader_chats 加 session_id，数据迁移
  - 步骤：① 2 张新表 → ② ALTER TABLE 迁移 + orphan 绑定 → ③ 9 个新方法
  - 验收：`from src.store.reader_store import ReaderStore; ReaderStore()` 无报错
  - 依赖：T-71

- [x] **T-77: 后端 API 端点（会话 + 推荐问题）**
  - 目标：7 个新端点 + 旧端点兼容 + 推荐问题 LLM 生成 + 缓存
  - 步骤：① 4 个新 schema → ② 7 个新路由 → ③ suggestions prompt + config → ④ 旧端点内部走 session
  - 验收：Swagger 可测试所有端点
  - 依赖：T-76

- [x] **T-78: 前端多会话 + 推荐问题**
  - 目标：SessionSwitcher + SuggestedQuestions 组件，ChatPanel/ReaderViewPage 集成
  - 步骤：① 类型 + API + hooks → ② SessionSwitcher 下拉菜单 → ③ SuggestedQuestions 芯片 → ④ ChatPanel 集成 → ⑤ ReaderViewPage session 状态管理 → ⑥ i18n
  - 验收：`npm run build` 无错误
  - 依赖：T-77

- [x] **T-71: Reader 数据存储层**
  - 目标：SQLite 存储文档元数据、分页文本、对话历史
  - 步骤：① reader_store.py 3 张表 → ② CRUD 方法
  - 验收：`from src.store.reader_store import ReaderStore` 成功
  - 依赖：无

- [x] **T-72: 文件分页提取服务**
  - 目标：PDF/PPTX/DOCX/MD/TXT 分页提取
  - 步骤：① reader_service.py → ② 5 种格式分页逻辑
  - 验收：各格式文件可正确分页
  - 依赖：T-71

- [x] **T-73: Reader API 端点**
  - 目标：10 个 API 端点 + AI 问答
  - 步骤：① schemas → ② routes/reader.py → ③ app.py 注册 → ④ settings.yaml + prompt
  - 验收：Swagger UI 可测试所有端点
  - 依赖：T-71, T-72

- [x] **T-74: 前端基础设施 + 文档列表页**
  - 目标：react-pdf 安装 + 类型 + API 客户端 + 列表页 + 路由 + 导航
  - 步骤：① npm install → ② 类型/API/hooks → ③ ReaderListPage → ④ 路由 + 侧边栏 → ⑤ i18n
  - 验收：`npm run build` 无错误
  - 依赖：T-73

- [x] **T-75: 核心阅读视图页**
  - 目标：左右分栏阅读视图 + PDF 渲染 + 文本渲染 + AI 对话
  - 步骤：① PdfPageViewer → ② TextPageViewer → ③ PageNavigation → ④ ChatPanel + ChatMessage → ⑤ ReaderViewPage 组装
  - 验收：上传 PDF 可翻页浏览 + AI 问答，上传 TXT 可文本渲染
  - 依赖：T-74

## Phase 10: 论文搜索功能 `[完成]`

- [x] **T-81: 新增 PubMed + bioRxiv Provider**
  - 目标：新增 PubMedProvider (NCBI E-utilities) 和 BiorxivProvider (Europe PMC REST API)
  - 步骤：① PubMedProvider esearch+efetch → ② BiorxivProvider Europe PMC → ③ SearchManager provider_names 过滤 → ④ settings.yaml 配置
  - 验收：新 Provider 可正常搜索返回 ExternalSearchResult
  - 依赖：无

- [x] **T-82: 论文搜索 API 端点**
  - 目标：3 个 REST 端点 — 搜索/保存到知识库/下载分析
  - 步骤：① schemas → ② paper_search.py 路由 → ③ app.py 注册
  - 验收：Swagger UI 可测试所有端点
  - 依赖：T-81

- [x] **T-83: CLI paper-search 命令**
  - 目标：CLI 搜索外部学术论文，支持 --providers --limit --save --json
  - 步骤：① main.py paper-search 命令 → ② Rich Table 输出 → ③ --save 存入 KB
  - 验收：`uv run python main.py paper-search "deep learning" -n 3` 正常输出
  - 依赖：T-81

- [x] **T-84: 前端论文搜索页面**
  - 目标：完整的论文搜索 Web UI — 搜索框 + 来源过滤 + 结果卡片 + 保存/下载
  - 步骤：① API 客户端 → ② usePaperSearch hook → ③ SearchResultCard 组件 → ④ PaperSearchPage → ⑤ 路由+侧边栏+i18n
  - 验收：`npm run build` 无错误，搜索页面功能完整
  - 依赖：T-82

---

## Backlog（想法池）

> 以下是未排期的功能点和优化想法，随时可以追加。进入开发时移到对应 Phase。

- [ ] 音频转录 Agent（faster-whisper）
- [x] 会议报告专用模板
- [x] 批量处理：`python main.py batch ./papers/`
- [x] 知识库导出/导入（JSON/CSV）
- [x] Web UI 界面
- [x] 异步并行处理多文档
- [x] 模型调用成本统计
- [x] 自定义报告模板系统
