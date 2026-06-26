# Literature Mapper / 文献检索与综述工具

A professional academic literature search and survey assistant powered by **arXiv** and **OpenAlex** dual-source retrieval, with a two-tier strategy and journal/conference tier filtering.

基于 **arXiv + OpenAlex 双源检索**的专业学术文献检索与综述助手，采用双层策略，支持期刊/会议等级过滤。

---

## Overview / 概述

**English**

Literature Mapper automates the end-to-end workflow of academic literature research: from defining search criteria, building a journal/conference whitelist based on tier (CAS zones / CCF levels), executing dual-source retrieval (arXiv for coverage + OpenAlex for quality), cleaning, sorting, clustering, and finally generating structured survey reports in Markdown, Word, or Excel format.

**中文**

Literature Mapper 自动完成文献调研的端到端工作流：从定义检索需求、基于等级（中科院分区 / CCF 等级）构建期刊/会议白名单、执行双源检索（arXiv 保覆盖 + OpenAlex 保质量）、数据清洗、排序、聚类分析，到最终输出结构化综述报告（Markdown / Word / Excel）。

---

## Workflow / 工作流

| Phase | Step | Description |
|-------|------|-------------|
| 0 | Requirements | Collect user keywords, document type, tier limits, time range, sort criteria |
| 1 | Build Whitelist | Filter journals/conferences from CAS + CCF tier tables by level only |
| 2 | Build Search Query | Generate arXiv and OpenAlex query strings from keywords |
| 3 | Execute Search | arXiv baseline (20 papers) + OpenAlex premium (30 papers, whitelist-filtered) |
| 4 | Data Cleaning | Dedup, normalize, backfill tier info |
| 5 | Sort & Pre-select | Sort by year/citations/tier, user selects focus papers |
| 6 | Cluster & Analyze | Topic clustering, trend inference, controversy identification |
| 7 | Generate Report | Structured survey report with overview, topic groups, references |
| 8 | Export | Output as Markdown (.md), Word (.docx), or Excel (.xlsx) |

---

## Directory Structure / 目录结构

```
.
├── assets/                          # Static data — tier lookup tables
│   ├── 2025中科院分区表.csv          # CAS journal zone table (2025)
│   └── 中国计算机学会国际学术会议分区.csv  # CCF conference/journal tier table
├── references/                      # Documentation & templates
│   ├── filter_rules.md              # Matching rules for dedup, sorting, tier backfill
│   └── output_templates.md          # Output format specifications
├── tools/                           # CLI tools (each phase has a dedicated script)
│   ├── build_whitelist.py           # Phase 1: build tier-based whitelist
│   ├── search_arxiv.py              # Phase 3: arXiv API search
│   ├── search_openalex.py           # Phase 3: OpenAlex API search
│   ├── merge_dedup.py               # Phase 3: merge + dedup
│   ├── backfill_tier.py             # Phase 4: backfill tier info
│   ├── sort_papers.py               # Phase 5: sort papers
│   └── output_report.py             # Phase 8: export report (md/docx/xlsx)
├── SKILL.md                         # Agent instruction file (Codex skill)
├── requirements.txt                 # Python dependencies
└── README.md                        # This file
```

---

## Quick Start / 快速开始

```bash
# Install dependencies / 安装依赖
pip install -r requirements.txt

# Phase 0: Create a filter config (or follow SKILL.md interactive process)
# Phase 1: Build whitelist / 构建白名单
python tools/build_whitelist.py --filters filters.json

# Phase 3: Search arXiv / 检索 arXiv
python tools/search_arxiv.py --query "ti:large language model" --max-results 30

# Phase 3: Search OpenAlex / 检索 OpenAlex
python tools/search_openalex.py --query "large language model" --journal-whitelist '["Nature"]'

# Phase 4: Backfill tier / 回填等级
python tools/backfill_tier.py --input merged.json --output tiered.json

# Phase 5: Sort papers / 排序
python tools/sort_papers.py --input tiered.json --sort-by citations --output sorted.json

# Phase 8: Export report / 导出报告
python tools/output_report.py --input sorted.json --format all --topic "My Research Topic" --overview "Survey overview..."
```

---

## Key Design Decisions / 关键设计

- **Search-first, whitelist-second**: The whitelist controls **quality level only** — field relevance is guaranteed by the search query itself. This avoids missing relevant papers in high-tier venues that cross discipline boundaries.
- **Dual-source strategy**: arXiv ensures coverage (preprints, broad keywords), OpenAlex ensures quality (peer-reviewed, tier-filtered).
- **No PDF reading**: Analysis is based on titles and abstracts only. Full paper content is never accessed.
- **Plan mode**: Phases marked `[Checkpoint]` in SKILL.md pause for user confirmation (requirements, paper selection, report refinement).

---

## License / 许可证

### 版权信息
本项目由 **Zywang812**（GitHub）创作并维护。

### 使用许可
- **公开免费使用**：任何人都可以免费使用本项目，包括个人学习、研究及非商业用途。
- **商业使用**：如需将本项目用于商业目的（包括但不限于集成到商业产品、提供付费服务等），**必须事先获得作者授权**。

### 联系方式
- **GitHub**：[@Zywang812](https://github.com/Zywang812)
- **小红书**：63584811973
- **邮箱**：zywang812@163.com

### 建议与反馈
如果您有改进建议、功能需求或发现任何问题，欢迎通过以上方式联系我。您的反馈将帮助项目变得更好！

---
**免责声明**：本项目按“现状”提供，作者不对使用本项目所产生的任何直接或间接损失承担责任。使用即代表您已阅读并同意本声明。
