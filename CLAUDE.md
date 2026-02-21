# CLAUDE.md - Project Context & AI Rules

## AI Config

```yaml
# === AI Behavior Configuration ===
auto_commit: true                    # 每个有意义的改动自动 git commit
auto_push: false                     # 设为 true 则自动 push（仅限 feature branch）
commit_format: "type(task-id): description"  # feat/fix/refactor/docs/test/chore
update_progress: true                # task 完成后自动更新 PROGRESS.md
update_changelog: true               # 功能变更后自动追加 CHANGELOG.md [Unreleased]
update_devlog: on_session_end        # 每个工作会话结束时更新 devlog
update_tasks: true                   # task 完成后自动在 TASKS.md 中标记 [x]
```

## Project Overview
- **Name**: research-analysis
- **Type**: backend-python (CLI 工具)
- **Description**: 研讨会/组会分析工具，从研究材料自动生成组会报告和结构化知识库

## Tech Stack
- Python 3.11+ (uv 包管理)
- openai SDK (统一调用国内大模型)
- Pydantic v2 (数据模型)
- Typer + Rich (CLI)
- PyMuPDF (PDF 解析)
- python-pptx (PPT 解析/生成)
- SQLite + FTS5 (知识库)
- Loguru (日志)
- PyYAML (配置)

## Project Structure
```
research-analysis/
├── config/
│   ├── settings.yaml              # 模型配置
│   └── prompts/                   # Prompt 模板
├── src/
│   ├── core/                      # 核心引擎
│   │   ├── engine.py              # Pipeline 工作流
│   │   ├── llm_client.py          # 统一 LLM 客户端
│   │   └── models.py              # Pydantic 模型
│   ├── agents/                    # 5 个 Agent
│   ├── parsers/                   # 格式解析器
│   ├── outputs/                   # 输出适配器
│   └── store/                     # 知识库
├── main.py                        # CLI 入口
└── pyproject.toml
```

## Common Commands
```bash
uv sync                              # 安装依赖
uv run python main.py analyze X.pdf  # 分析文档
uv run python main.py search "keyword"  # 搜索知识库
uv run pytest                        # 运行测试
uv run ruff check src/               # 代码检查
```

## Workflow Rules

- 每次完成一个 task 后：
  1. 在 TASKS.md 中将对应 task 标记为 `[x]`
  2. 更新 PROGRESS.md（完成数、百分比、已完成列表）
  3. 更新 CHANGELOG.md 的 `[Unreleased]` 区块（如果有用户可见的变更）
  4. 自动 git commit，message 格式：`type(T-XX): 简短描述`
- 每个工作会话结束前：
  1. 创建或更新 `devlogs/YYYY-MM-DD.md`
  2. 确保所有改动已 commit
- 如果 `auto_push: true`：commit 后自动 push（但绝不 force push，绝不 push 到 main/master）

## Git Rules

- **Commit 粒度**：一个 task = 一次 commit（不拆太细，不攒太多）
- **Commit message 格式**：`type(T-XX): description`
  - type: feat / fix / refactor / docs / test / chore
  - 示例：`feat(T-05): 实现分析 Agent`
- **Branch 策略**：新功能在 feature branch 开发，完成后合并
- **禁止**：force push、直接 push 到 main/master、--no-verify

## Auto-Update Rules

| 文件 | 更新时机 | 更新内容 |
|------|---------|---------|
| TASKS.md | 完成 task 时 | 标记 `[x]`，更新状态标签 |
| PROGRESS.md | 完成 task 时 | 完成数/百分比/已完成列表/当前进行中 |
| CHANGELOG.md | 有用户可见变更时 | 追加到 `[Unreleased]` 对应分类下 |
| devlogs/日期.md | 会话结束时 | 今日完成、遇到的问题、明日计划 |

## Code Conventions
- 使用 Python 类型注解
- Agent 间通过 Pydantic Model 传递数据
- 所有 LLM 调用通过 LLMClient 统一管理
- 配置文件使用 YAML 格式
- API Key 只从环境变量读取，不存配置文件

## Important Notes
- 所有国内模型均通过 OpenAI 兼容接口调用
- Agent 模型分配在 config/settings.yaml 中配置
- Pipeline 为同步线性管线 + Reviewer 反馈循环
