# research-analysis

研讨会/组会分析工具 - 从研究材料（论文、PPT、录音、笔记）自动生成组会报告和结构化知识库。

采用多 Agent 工作流架构，使用国内大模型（DeepSeek/通义千问/智谱GLM），按 Agent 分配不同模型以平衡成本和效果。

## Getting Started

### Prerequisites

- Python >= 3.11
- [uv](https://docs.astral.sh/uv/) 包管理器

### Installation

```bash
# 克隆项目
git clone <repo-url>
cd research-analysis

# 安装依赖（uv 自动创建虚拟环境）
uv sync

# 复制环境变量配置
cp .env.example .env
# 编辑 .env 填入你的 API Key
```

### 可选依赖

```bash
# 音频转录支持
uv sync --extra audio

# Word 文档输出支持
uv sync --extra docx

# 开发工具
uv sync --extra dev
```

## Usage

```bash
# 分析单篇论文
uv run python main.py analyze paper.pdf

# 多篇论文综合分析
uv run python main.py analyze paper1.pdf paper2.pdf --synthesize

# 指定输出格式
uv run python main.py analyze paper.pdf --format docx

# 知识库搜索
uv run python main.py search "transformer attention"

# 列出所有文档
uv run python main.py list --tag "NLP"
```

## Tech Stack

- **Runtime**: Python 3.11+
- **LLM**: OpenAI 兼容接口（DeepSeek / 通义千问 / 智谱GLM）
- **CLI**: Typer + Rich
- **数据模型**: Pydantic v2
- **PDF 解析**: PyMuPDF
- **PPT 解析/生成**: python-pptx
- **知识库**: SQLite + FTS5

## Project Structure

```
research-analysis/
├── config/
│   ├── settings.yaml              # 模型配置、Agent 模型分配
│   └── prompts/                   # 各 Agent 的 Prompt 模板
├── src/
│   ├── core/
│   │   ├── engine.py              # Pipeline 工作流引擎
│   │   ├── llm_client.py          # 统一 LLM 调用层
│   │   └── models.py              # Pydantic 数据模型
│   ├── agents/
│   │   ├── base.py                # Agent 基类
│   │   ├── parser.py              # 解析 Agent
│   │   ├── analyzer.py            # 分析 Agent
│   │   ├── synthesizer.py         # 综合 Agent
│   │   ├── generator.py           # 生成 Agent
│   │   └── reviewer.py            # 评审 Agent
│   ├── parsers/                   # 格式解析器
│   ├── outputs/                   # 输出适配器
│   └── store/
│       └── knowledge_base.py      # SQLite 知识库
├── templates/                     # 报告模板
├── knowledge_base/                # 数据存储
├── tests/
├── main.py                        # CLI 入口
└── pyproject.toml
```

## Architecture

5 个 Agent 串联的线性 Pipeline，每个 Agent 使用不同模型，通过 Pydantic model 传递数据：

```
文件输入 (PDF/PPT/TXT/MD)
  │
  ▼
┌─────────────────┐
│  ParserAgent     │  qwen-turbo（轻量）
│  解析文件内容     │  文件 → ParsedDocument
└────────┬────────┘
         ▼
┌─────────────────┐
│  AnalyzerAgent   │  deepseek-chat（强力）
│  深度分析         │  ParsedDocument → AnalysisResult
└────────┬────────┘
         ▼
┌─────────────────┐
│ SynthesizerAgent │  deepseek-chat（强力）
│ 跨文档综合       │  多个 AnalysisResult → SynthesisResult
└────────┬────────┘  （单文档时跳过）
         ▼
┌─────────────────┐
│ GeneratorAgent   │  qwen-plus（中等）
│ 生成报告         │  → Report (Markdown)
└────────┬────────┘
         ▼
┌─────────────────┐       不合格（最多 2 次）
│ ReviewerAgent    │  glm-4-flash ──────────┐
│ 质量审查         │                         │
└────────┬────────┘                         │
         │ 合格                      ┌──────▼────────┐
         ▼                           │ GeneratorAgent  │
   输出报告                          │  重新生成        │
  (MD/DOCX/PPTX)                    └─────────────────┘
```

| Agent | 职责 | 模型 | 服务商 |
|-------|------|------|--------|
| Parser | 从 PDF/PPT/TXT 提取结构化文本 | qwen-turbo | 阿里 DashScope |
| Analyzer | 深度分析单篇文档 | deepseek-chat | DeepSeek |
| Synthesizer | 跨文档对比和主题归纳 | deepseek-chat | DeepSeek |
| Generator | 按模板生成报告 | qwen-plus | 阿里 DashScope |
| Reviewer | 质量检查，不合格打回重做 | glm-4-flash | 智谱 AI |

## Environment Variables

See [.env.example](.env.example) for required environment variables.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
