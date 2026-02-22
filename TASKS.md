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

## Phase 6: 国际化 + 优化 `[进行中]`

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

---

## Backlog（想法池）

> 以下是未排期的功能点和优化想法，随时可以追加。进入开发时移到对应 Phase。

- [ ] 音频转录 Agent（faster-whisper）
- [x] 会议报告专用模板
- [x] 批量处理：`python main.py batch ./papers/`
- [x] 知识库导出/导入（JSON/CSV）
- [x] Web UI 界面
- [ ] 异步并行处理多文档
- [x] 模型调用成本统计
- [ ] 自定义报告模板系统
