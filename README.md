# Literature Mapper / 文献检索与综述工具

> **A professional academic literature search and survey assistant**
> **专业学术文献检索与综述助手**

> 基于 arXiv 和 OpenAlex 双源检索 | 支持中科院分区 / CCF 等级过滤 | 输出 Markdown / Word / Excel 格式综述报告

---

## Overview / 概述

**English**

Literature Mapper automates the end-to-end workflow of academic literature research: from defining search criteria, building a journal/conference whitelist based on tier (CAS zones / CCF levels), executing dual-source retrieval (arXiv for coverage + OpenAlex for peer-reviewed quality), cleaning, sorting, clustering, and finally generating structured survey reports in Markdown, Word, or Excel format.

This tool is designed to work as a **skill/plugin within AI assistants** such as Codex, Claude, and Z-Code. You interact with it through natural language conversation.

**中文**

Literature Mapper 自动完成文献调研的端到端工作流：从定义检索需求、基于等级（中科院分区 / CCF 等级）构建期刊/会议白名单、执行双源检索（arXiv 覆盖预印本 + OpenAlex 过滤同行评审文献）、数据清洗、排序、聚类分析，到最终输出结构化综述报告（Markdown / Word / Excel）。

本工具是面向 **AI 助手（如 Codex、Claude、Z-Code）** 的技能/插件，通过自然语言对话即可完成完整的文献调研流程。

---

## Features / 功能特色

- **Dual-source retrieval / 双源检索**: arXiv (preprints) + OpenAlex (peer-reviewed, tier-filtered)
- **Tier-based filtering / 等级过滤**: CAS journal zones + CCF conference/journal levels
- **End-to-end workflow / 全流程自动**: From requirements to structured report in one conversation
- **Multi-format export / 多格式导出**: Markdown, Word (.docx), Excel (.xlsx)
- **Intelligent clustering / 智能聚类**: Topic clustering, trend inference, controversy identification
- **No PDF access / 不涉及全文**: Based on titles and abstracts only

---

## Quick Start / 快速开始

### Using in AI Assistants (Codex / Claude / Z-Code)

This is a skill for AI assistants. Simply describe your research needs in natural language:

**Examples (Chinese)**:

```
我想查一下关于大语言模型在医学诊断中的应用的文献。
要求期刊中科院一区/二区，会议CCF A/B类，近5年的文献。
帮我输出Word和Excel格式的报告。
```

```
我最近在研究联邦学习在医疗领域的应用，需要做一次文献调研。
论文类型：期刊和会议都要，期刊要中科院一区/二区，会议要CCF A/B类。
时间范围：2021-2026年。排序方式：按引用量排序。
```

**Examples (English)**:

```
I want to search for literature about the application of large language models in medical diagnosis.
Journal: CAS Zone 1/2, Conference: CCF Level A/B, published in the last 5 years.
Export the report in Word and Excel formats.
```

The AI assistant will guide you through the workflow step by step, with checkpoints at key decision points for your confirmation.

### Manual CLI Usage

```bash
# Install dependencies
pip install -r requirements.txt

# Build whitelist
python tools/build_whitelist.py --filters filters.json

# Search arXiv
python tools/search_arxiv.py --query "ti:large language model" --max-results 30

# Search OpenAlex with whitelist
python tools/search_openalex.py --query "large language model" --journal-whitelist '["Nature"]'

# Merge and dedup
python tools/merge_dedup.py --arxiv arxiv_results.json --openalex openalex_results.json --output merged.json

# Backfill tier info
python tools/backfill_tier.py --input merged.json --output tiered.json

# Sort papers
python tools/sort_papers.py --input tiered.json --sort-by citations --output sorted.json

# Export report
python tools/output_report.py --input sorted.json --format all --topic "LLM in Medical Diagnosis"
```

---

## Workflow / 工作流

| Phase | Step | Description |
|-------|------|-------------|
| 0 | Requirements [Checkpoint] | Collect keywords, document type, tier limits, time range, sort criteria |
| 1 | Build Whitelist | Filter journals/conferences from CAS + CCF tier tables |
| 2 | Build Search Query | Generate arXiv and OpenAlex query strings |
| 3 | Execute Search | arXiv ~20 papers + OpenAlex ~30 papers |
| 4 | Data Cleaning | Dedup, normalize, backfill tier info |
| 5 | Sort & Select [Checkpoint] | Sort by year/citations/tier, user selects focus papers |
| 6 | Cluster & Analyze | Topic clustering, trend inference, controversy identification |
| 7 | Generate Report [Checkpoint] | Structured survey report |
| 8 | Export [Checkpoint] | Markdown (.md), Word (.docx), Excel (.xlsx) |

---

## Directory Structure / 目录结构

```
.
├── assets/                          # Tier lookup tables
├── references/                      # Docs & templates
│   ├── filter_rules.md
│   └── output_templates.md
├── tools/                           # CLI scripts
│   ├── build_whitelist.py           # Phase 1
│   ├── search_arxiv.py              # Phase 3: arXiv API
│   ├── search_openalex.py           # Phase 3: OpenAlex API
│   ├── merge_dedup.py               # Phase 3: merge + dedup
│   ├── backfill_tier.py             # Phase 4: backfill tier
│   ├── sort_papers.py               # Phase 5: sort
│   └── output_report.py             # Phase 8: export
├── SKILL.md                         # Agent instruction file
├── requirements.txt
└── README.md
```

---

## Key Design Decisions / 关键设计

- **Search-first, whitelist-second**: The whitelist controls quality level only -- field relevance is guaranteed by the search query itself. This avoids missing relevant papers in high-tier venues that cross discipline boundaries.
- **Dual-source strategy**: arXiv ensures coverage (preprints, broad keywords), OpenAlex ensures quality (peer-reviewed, tier-filtered).
- **No PDF reading**: Analysis is based on titles and abstracts only. Full paper content is never accessed.
- **Plan mode**: Phases marked [Checkpoint] pause for user confirmation.

---

## License / 许可证

Copyright (c) 2026 Zywang812

- **Public free use**: Personal learning, research, and non-commercial use.
- **Commercial use**: Must obtain prior authorization from the author.
- **公开免费使用**：个人学习、研究及非商业用途。
- **商业使用**：必须事先获得作者授权。

### Contact / 联系方式

- **GitHub**: [@Zywang812](https://github.com/Zywang812)
- **Email**: zywang812@163.com

---

 **Disclaimer / 免责声明**: This project is provided "as is" without warranty.

---

## Usage Examples / 使用示例

Below is a walkthrough of a complete literature search session using the CLI tools.

以下是一个完整的文献检索流程演示。

### Example: LLM in Medical Diagnosis

**User Input (自然语言输入)**:

```
I want to search for literature about large language models in medical diagnosis.
Journal: CAS Zone 1/2, Conference: CCF Level A/B, Last 5 years.
Sort by citations. Export in Word and Excel formats.
```

**Step-by-step Execution (分步执行)**:

```
# Step 1: Build whitelist from tier tables
python tools/build_whitelist.py --filters filters.json

# Step 2: Search arXiv for preprints
python tools/search_arxiv.py --query "ti:large language model" --max-results 30

# Step 3: Search OpenAlex with whitelist filtering
python tools/search_openalex.py --query "large language model medical diagnosis"

# Step 4: Merge and dedup results
python tools/merge_dedup.py --arxiv arxiv_results.json --openalex openalex_results.json --output merged.json

# Step 5: Backfill tier info from local tables
python tools/backfill_tier.py --input merged.json --output tiered.json

# Step 6: Sort papers by user preference
python tools/sort_papers.py --input tiered.json --sort-by citations --output sorted.json --top 20

# Step 7: Export final report
python tools/output_report.py --input sorted.json --format all --topic "LLM in Medical Diagnosis"
```

**Generated Outputs (生成文件)**:

- **Markdown** (`.md`): Full report with paper table and references
- **Word** (`.docx`): Formatted document with heading structure
- **Excel** (`.xlsx`): Summary table with article links column

The Excel output includes a dedicated **文章链接** (Article Link) column containing DOI URLs for easy access to each paper.

Excel 输出包含"文章链接"列，点击可直接跳转到每篇文献的 DOI 页面。
