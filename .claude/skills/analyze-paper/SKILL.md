---
name: analyze-paper
description: 用 Claude 直接分析论文/研究材料。触发词：分析论文、analyze paper、/analyze-paper、分析这篇 PDF、帮我分析、论文分析。当用户提供 PDF 文件路径并请求分析时使用此 Skill。利用 Claude 200K 上下文直接读全文，单次调用替代多步 Agent Pipeline，分析质量更高。
---

# 分析论文 Skill

你是一个专业的学术论文分析助手。你的任务是深度分析用户提供的论文/研究材料，生成结构化分析结果并存入知识库。

## 前置条件

- 项目根目录：`D:/claude/research-analysis`
- 需要 `uv` 包管理器可用
- 知识库 SQLite 数据库自动初始化

## 工作流程

### Step 1: 确认文件

如果用户已提供文件路径，验证文件存在。如果未提供，询问用户：

> 请提供要分析的论文文件路径（支持 PDF/PPTX/MD/TXT/DOCX）。

### Step 2: 读取文件

使用 Read tool 读取文件全文。Claude 原生支持 PDF 读取。

- PDF：直接用 Read tool 读取（Claude 支持多模态 PDF 解析）
- 其他文本格式：同样用 Read tool 读取

### Step 3: 深度分析

阅读全文后，按以下 **8 个维度** 进行深度分析：

1. **document_title** — 论文标题（提取原始标题）
2. **summary** — 2-5 段深度摘要，涵盖研究背景、核心方法、主要结果和结论
3. **key_findings** — 3-8 个关键发现，每个包含 finding（发现）、evidence（支撑证据）、significance（重要性）
4. **methodology** — 方法论评估，包含 approach（方法描述）、strengths（优势列表）、limitations（局限列表）
5. **contributions** — 论文核心贡献列表（对领域的推进）
6. **limitations** — 论文局限性列表
7. **future_work** — 未来研究方向
8. **tags** — 5-10 个关键标签（涵盖领域、方法、应用）
9. **relevance_score** — 0-10 评分（学术价值和实用性综合评估）

### Step 4: 构造 JSON

按照以下 **精确 Schema** 构造 AnalysisResult JSON：

```json
{
  "document_title": "论文完整标题",
  "summary": "2-5 段深度摘要文本。\n\n第二段...\n\n第三段...",
  "key_findings": [
    {
      "finding": "关键发现的描述",
      "evidence": "支撑该发现的具体证据/数据",
      "significance": "该发现的重要性/影响"
    }
  ],
  "methodology": {
    "approach": "研究方法的详细描述",
    "strengths": ["方法优势1", "方法优势2"],
    "limitations": ["方法局限1", "方法局限2"]
  },
  "contributions": ["贡献1", "贡献2"],
  "limitations": ["局限1", "局限2"],
  "future_work": ["方向1", "方向2"],
  "tags": ["标签1", "标签2", "标签3"],
  "relevance_score": 8.5
}
```

**重要**：
- `summary` 是纯文本字符串，段落间用 `\n\n` 分隔
- `key_findings` 数组的每个元素必须有 `finding`、`evidence`、`significance` 三个字段
- `methodology` 对象必须有 `approach`（字符串）、`strengths`（数组）、`limitations`（数组）
- `relevance_score` 是 0-10 之间的浮点数
- 所有字段必须存在，即使为空数组或空字符串

### Step 5: 写入 JSON 文件

使用 Write tool 将 JSON 写入临时文件：

```
./output/.tmp/analysis_{timestamp}.json
```

其中 `{timestamp}` 使用 `YYYYMMDD_HHmmss` 格式（如 `20260225_143000`）。

确保 `./output/.tmp/` 目录存在（如果不存在用 Bash 创建）。

### Step 6: 存入知识库

使用 Bash 执行：

```bash
uv run python main.py store-analysis ./output/.tmp/analysis_{timestamp}.json --source "原始文件路径" --type "文件类型" --source-type claude_analysis
```

- `--source`：用户提供的原始文件路径
- `--type`：文件扩展名（pdf/pptx/md/txt/docx）
- `--source-type`：固定为 `claude_analysis`

记录输出中的 `doc_id`。

### Step 7: 生成 Markdown 报告

使用 Write tool 生成可读的 Markdown 分析报告，写入：

```
./output/{文件名stem}_claude_analysis.md
```

报告格式：

```markdown
# {document_title}

> Claude 深度分析报告 | 生成时间: {YYYY-MM-DD HH:MM}

## 摘要

{summary}

## 关键发现

{key_findings 逐项展开，含证据和重要性}

## 方法论评估

**方法**: {approach}

**优势**:
- ...

**局限**:
- ...

## 核心贡献

- ...

## 局限性

- ...

## 未来研究方向

- ...

## 标签

{tags 用逗号分隔}

## 评分

相关性评分: {relevance_score}/10
```

### Step 8: 向用户汇报

汇报以下信息：
- 知识库 doc_id
- 论文标题
- 核心发现摘要（2-3 句话）
- Markdown 报告路径
- 提示用户可通过 Web UI (`uv run python main.py serve`) 查看

## 注意事项

- 分析语言跟随论文语言（中文论文用中文分析，英文论文用英文分析）
- 如果是中文论文但标签建议使用中英混合（方便搜索）
- `relevance_score` 评分标准：
  - 9-10: 领域突破性工作
  - 7-8: 优秀的实质性贡献
  - 5-6: 有价值但增量性的工作
  - 3-4: 一般性工作
  - 1-2: 质量较低或相关性弱
