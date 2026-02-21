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
| M4: 高级功能 | 音频转录 + 批量处理 | Phase 4 |

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

## Phase 1: 基础骨架 + MVP `[当前]`

- [ ] **T-03: 创建 Pydantic 数据模型**
  - 目标：定义 Agent 间传递的数据结构
  - 步骤：① ParsedDocument → ② AnalysisResult → ③ SynthesisResult → ④ Report → ⑤ ReviewFeedback
  - 验收：所有模型可实例化，字段类型正确
  - 依赖：T-01

- [ ] **T-04: 构建统一 LLM 客户端**
  - 目标：封装多模型调用，通过 OpenAI 兼容接口统一访问
  - 步骤：① 读取 settings.yaml 配置 → ② 懒加载 OpenAI 客户端 → ③ chat() 和 chat_json() 方法
  - 验收：Mock 测试验证 base_url 正确，消息格式正确
  - 依赖：T-01

- [ ] **T-05: 创建 Agent 基类**
  - 目标：提供 LLM 调用、消息构建、Prompt 加载能力
  - 步骤：① BaseAgent 类 → ② process() 抽象方法 → ③ Prompt 模板加载
  - 验收：基类可被继承，提供完整的 LLM 交互能力
  - 依赖：T-04

- [ ] **T-06: 实现 PDF 解析器**
  - 目标：从 PDF 提取结构化文本
  - 步骤：① PyMuPDF 读取 → ② 提取标题/段落/图表描述 → ③ 返回 ParsedDocument
  - 验收：真实 PDF 能正确解析为 ParsedDocument
  - 依赖：T-03

- [ ] **T-07: 实现解析 Agent**
  - 目标：调度解析器，对提取文本做初步结构化
  - 步骤：① 根据文件类型选择解析器 → ② 调用解析器 → ③ 返回 ParsedDocument
  - 验收：输入文件路径，输出正确的 ParsedDocument
  - 依赖：T-05, T-06

- [ ] **T-08: 实现分析 Agent**
  - 目标：对单篇文档进行深度分析
  - 步骤：① 构建分析 Prompt → ② 调用 LLM → ③ 解析为 AnalysisResult
  - 验收：输入 ParsedDocument，输出包含摘要、关键发现、方法论评估的 AnalysisResult
  - 依赖：T-05, T-03

- [ ] **T-09: 实现生成 Agent**
  - 目标：按模板生成 Markdown 报告
  - 步骤：① 构建生成 Prompt → ② 调用 LLM → ③ 返回 Report
  - 验收：输入 AnalysisResult，输出格式良好的 Markdown 报告
  - 依赖：T-05, T-03

- [ ] **T-10: 构建 Pipeline 引擎**
  - 目标：串联 Parse → Analyze → Generate 工作流
  - 步骤：① 加载配置 → ② 按顺序执行 Agent → ③ rich 进度条显示
  - 验收：输入文件路径，自动走完 Pipeline 输出报告
  - 依赖：T-07, T-08, T-09

- [ ] **T-11: 创建 CLI 入口和 Markdown 输出**
  - 目标：`python main.py analyze paper.pdf` 可用
  - 步骤：① typer CLI 框架 → ② analyze 命令 → ③ Markdown 文件输出
  - 验收：命令行输入 PDF 文件，输出 Markdown 报告文件
  - 依赖：T-10

## Phase 2: 多模型 + 更多解析器 + 综合分析

- [ ] **T-12: 完善多模型配置**
  - 目标：不同 Agent 使用不同模型
  - 步骤：① settings.yaml 多模型配置 → ② Agent 自动按配置选模型 → ③ 日志记录模型选择
  - 验收：日志确认不同 Agent 调用了不同模型
  - 依赖：T-10

- [ ] **T-13: 实现 PPT 解析器**
  - 目标：从 .pptx 文件提取内容
  - 步骤：① python-pptx 读取 → ② 提取幻灯片文本/图表 → ③ 返回 ParsedDocument
  - 验收：真实 .pptx 能正确解析
  - 依赖：T-03

- [ ] **T-14: 实现笔记解析器**
  - 目标：解析 Markdown/TXT/DOCX 笔记
  - 步骤：① 按格式分发 → ② 提取结构化内容 → ③ 返回 ParsedDocument
  - 验收：Markdown/TXT 文件能正确解析
  - 依赖：T-03

- [ ] **T-15: 实现综合 Agent**
  - 目标：跨文档对比和主题归纳
  - 步骤：① 多文档输入 → ② 交叉对比 Prompt → ③ 返回 SynthesisResult
  - 验收：输入多个 AnalysisResult，输出跨文档综合分析
  - 依赖：T-05, T-03

- [ ] **T-16: 更新 Pipeline 支持 Synthesizer**
  - 目标：多文档时自动启用综合分析
  - 步骤：① 检测多文档输入 → ② 插入 Synthesizer 步骤 → ③ Generator 使用 SynthesisResult
  - 验收：多文件输入产出包含跨文档对比的报告
  - 依赖：T-15, T-10

## Phase 3: 评审 + 知识库 + 多格式输出

- [ ] **T-17: 实现评审 Agent**
  - 目标：对生成报告做质量检查
  - 步骤：① 评审 Prompt → ② 打分 + 反馈 → ③ 返回 ReviewFeedback
  - 验收：能识别报告质量问题并给出具体反馈
  - 依赖：T-05, T-03

- [ ] **T-18: Pipeline 加入评审反馈循环**
  - 目标：不合格报告打回重做（最多 2 次）
  - 步骤：① Reviewer 评审 → ② 不合格传反馈给 Generator → ③ 重新生成
  - 验收：Mock Reviewer 拒绝 → Generator 收到反馈 → 重新生成
  - 依赖：T-17, T-10

- [ ] **T-19: 实现 SQLite 知识库**
  - 目标：存储分析结果，支持全文搜索
  - 步骤：① SQLite + FTS5 表结构 → ② 存储/查询接口 → ③ 标签系统
  - 验收：存储 → 搜索 → 验证 FTS5 结果正确
  - 依赖：T-03

- [ ] **T-20: 实现 DOCX/PPTX 输出**
  - 目标：支持 Word 和 PPT 格式输出
  - 步骤：① docx_writer → ② pptx_writer → ③ CLI 增加 --format 选项
  - 验收：输出的 DOCX/PPTX 文件可正常打开
  - 依赖：T-10

- [ ] **T-21: Prompt 模板外置 + CLI 扩展**
  - 目标：Prompt 可配置，CLI 增加 search/list 命令
  - 步骤：① Prompt 移至 config/prompts/ → ② search 命令 → ③ list 命令
  - 验收：修改 Prompt 文件无需改代码；search/list 命令可用
  - 依赖：T-19

---

## 未来阶段（进入时再展开详细 task）

### Phase 4: 音频 + 高级功能
- 目标：支持音频转录和批量处理
- 方向：faster-whisper 音频转录、会议报告专用模板、批量处理、知识库导出/导入

---

## Backlog（想法池）

> 以下是未排期的功能点和优化想法，随时可以追加。进入开发时移到对应 Phase。

- [ ] 音频转录 Agent（faster-whisper）
- [ ] 会议报告专用模板
- [ ] 批量处理：`python main.py batch ./papers/`
- [ ] 知识库导出/导入（JSON/CSV）
- [ ] Web UI 界面
- [ ] 异步并行处理多文档
- [ ] 模型调用成本统计
- [ ] 自定义报告模板系统
