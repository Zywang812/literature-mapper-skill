---
name: literature-mapper
description: >
  专业学术文献检索与综述助手。基于 arXiv 和 OpenAlex 双源检索，
  采用双层策略（20 篇保底 + 30 篇精品），严格遵循 Plan 模式，
  在关键决策点等待用户确认。当用户提到：查文献、检索论文、
  文献综述、学术论文搜索、arXiv 检索、OpenAlex 检索、
  期刊分区筛选、CCF 等级筛选、文献调研时使用。
---

# Literature Mapper

专业学术文献检索助手。基于**标题和摘要**进行分析，不涉及全文 PDF。

## 数据源

- **arXiv**：预印本，仅提供标题/摘要/DOI，无引用量和期刊/会议信息。
- **OpenAlex**：全学科文献库，提供引用量、期刊/会议、作者等丰富元数据。

## 核心策略

1. **白名单驱动**：检索前从 CSV 分级表中构建期刊/会议白名单，定向抓取。
2. **双层检索**：arXiv 保底 20 篇 + OpenAlex 精品 30 篇，兼顾数量与质量。
3. **Plan 模式**：标记为 **[Checkpoint]** 的步骤必须暂停等待用户确认。

## 全局规则

- **来源标识**：每篇文献标注来源（arXiv / OpenAlex / Both）。
- **合规标识**：标注"符合等级要求：是/否"（arXiv 保底文献默认为否）。
- **去重规则**：优先按 DOI 去重，若无则按标题精确匹配。
- **信息边界**：仅基于标题和摘要，严禁虚构全文内容。

---

## Phase 0: 需求对齐 [Checkpoint]

向用户提问以明确检索范围，**必须一次性收集以下所有信息**：

1. **自然语言关键词**：一句话描述研究主题（例如："我想查关于大语言模型在医学诊断中的应用"）。
2. **文献类型选择**：提供三个选项让用户选择：
   - **期刊论文（Journal）**：仅检索期刊文献。
   - **会议论文（Conference）**：仅检索会议文献。
   - **两者都要（Both）**：不限类型，全部检索。
3. **期刊等级限定**（若用户选择了期刊或两者都要）：中科院分区（一区 / 二区 / 三区 / 四区 / 不限）。
4. **会议等级限定**（若用户选择了会议或两者都要）：CCF 等级（A / B / C / 不限）。
5. **时间范围**：例如"近 5 年（2021-2026）"或"不限制"。
7. **排序标准**：按"发表年份"排序 / 按"引用量"排序 / 按"期刊/会议等级"排序。

收集完用户所有回答后，**必须**按以下 JSON 格式整理并展示给用户确认：

```json
{
  "keywords": "用户提供的自然语言关键词",
  "document_type": "用户选择的文献类型",
  "journal_level": "用户选择的期刊等级",
  "conference_level": "用户选择的会议等级",
  "time_range": "用户指定的时间范围",
  "sort_criteria": "用户选择的排序标准"
}
```

---

## Phase 1: 构建检索白名单

调用 `tools/build_whitelist.py`，传入用户在 Phase 0 中设定的条件（文献类型、期刊分区、CCF 等级），构建白名单：

### 期刊白名单（若 `article_type` 为 Journal 或 Both）

1. 查询 `assets/2025中科院分区表.csv`（表头：期刊名称、分区、是否开源），筛选出符合用户分区要求的期刊名称，加入期刊白名单。
2. 查询 `assets/中国计算机学会国际学术会议分区.csv`（表头：简称、全称、分类、类型），筛选出"类型"为"期刊"且符合用户 CCF 等级要求的记录，将其"全称"（若全称为空则用"简称"）加入期刊白名单。
3. 合并以上两个来源，去重后形成最终期刊白名单。

### 会议白名单（若 `article_type` 为 Conference 或 Both）

查询 `assets/中国计算机学会国际学术会议分区.csv`，筛选出"类型"为"会议"且符合用户 CCF 等级要求的记录。

### 输出与确认

将白名单结果展示给用户：

> 期刊白名单：共 X 本（来自中科院分区表 X 本，来自 CCF 分级表 X 本）
> 会议白名单：共 Y 个

白名单已自动生成，无需确认，自动进入下一阶段。
---

## Phase 2: 检索式构建与翻译

将用户提供的自然语言关键词（Phase 0 中的 keywords 和 synonyms）拆解为同义词族。

### 生成 arXiv 检索式

使用 `ti:` 或 `abs:` 前缀进行组合，例如：

```
ti:"large language model" AND abs:"medical diagnosis"
```

### 生成 OpenAlex 检索式

将关键词组合为 OpenAlex API 的 `search` 参数格式（OpenAlex 会自动进行全文语义搜索），例如：

```
large language model medical diagnosis
```

### 输出展示

将两个检索式清晰展示给用户。检索式已自动构建，无需确认，自动进入下一阶段。

---

## Phase 3: 执行检索（双层策略）

### 第一层：arXiv 保底检索（保证基础数量）

调用 `tools/search_arxiv.py`，仅基于 Phase 0 中提取的 keywords 和 synonyms 进行检索，不应用任何期刊/会议白名单过滤。

- **目的**：确保用户获得至少 20 篇高度相关的文献作为基础阅读材料，即使这些文献可能不符合等级要求。
- **限制**：抓取上限 30 篇，按相关性排序后取前 20 篇。
- **输出**：20 篇 arXiv 文献（含标题、作者、年份、DOI、摘要、PDF 链接），标记为"来源：arXiv | 符合等级要求：否"。

### 第二层：OpenAlex 精品检索（保证高质量）

调用 `tools/search_openalex.py`，检索时应用 Phase 1 构建的期刊白名单和会议白名单，仅抓取符合用户等级/分区/领域要求的文献。

- **目的**：提供 30 篇高质量、符合用户全部筛选条件的精品文献。
- **限制**：抓取上限 100 篇，应用白名单过滤后，按用户指定的排序标准排序，取前 30 篇。
- **输出**：30 篇精品文献（含标题、作者、年份、DOI、摘要、期刊/会议、引用量、分区/等级），标记为"来源：OpenAlex | 符合等级要求：是"。

### 第三层：合并与去重

调用 `tools/merge_dedup.py`，将 arXiv 保底文献与 OpenAlex 精品文献合并。

```bash
python tools/merge_dedup.py --arxiv arxiv_results.json --openalex openalex_results.json --output merged.json
```

- **去重规则**：按 DOI 或标题去重。若 arXiv 文献同时存在于 OpenAlex 精品列表中，保留 OpenAlex 版本（元数据更丰富），并标记为"来源：arXiv & OpenAlex | 符合等级要求：是"。
- **最终输出**：总计最多 50 篇文献（20 篇保底 + 30 篇精品，去重后可能少于 50 篇）。

示例输出：

> arXiv 保底检索：20 篇（均为预印本，不符合等级要求）
> OpenAlex 精品检索：30 篇（全部符合等级要求）
> 合并去重后：共计 47 篇有效文献（3 篇重复已剔除）

---

## Phase 4: 数据清洗与规范化

全自动阶段，无需 Checkpoint。对合并后的文献列表执行以下清洗操作：

1. **类型推断**：根据 OpenAlex 返回的 `type` 字段（如 article / proceeding）或期刊/会议名称，自动推断每篇文献的类型（Journal / Conference）。arXiv 文献若无类型信息，标注为"Unknown"。详细推断规则见 `references/filter_rules.md`。
2. **年份解析**：确保 `year` 字段为整数类型，若缺失则标注为"N/A"。
3. **引用量处理**：OpenAlex 文献保留 `cited_by_count`，arXiv 文献引用量统一填 `null`。
4. **等级回填**：调用 `tools/backfill_tier.py`，对 OpenAlex 精品文献查询本地分级表，回填其具体分区或 CCF 等级（如"中科院一区"或"CCF A 类"）。此步是 Phase 5 等级排序的数据前提。

```bash
python tools/backfill_tier.py --input merged.json --output papers_tiered.json
```

> 类型推断、年份解析、引用量处理由 `search_openalex.py` / `search_arxiv.py` 在检索阶段已规范化；本阶段工具调用重点是**等级回填**。回填规则详见 `references/filter_rules.md`。

输出：告知用户"数据清洗完成，有效文献共计 Z 篇。"

---

## Phase 5: 排序与预筛选 [Checkpoint]

调用 `tools/sort_papers.py`，严格按照用户在 Phase 0 中指定的排序标准，对全部 Z 篇文献进行排序，并生成 Top 20 推荐列表。

- **排序规则**：三种排序标准（年份降序 / 引用量降序 / 等级降序）、权重映射及"OpenAlex 精品优先"原则详见 `references/filter_rules.md`。
- **Top 20 列表格式**：每篇文献须包含的字段及 Markdown 表格模板详见 `references/output_templates.md`。

### 输出与确认

暂停：询问"请查看上方 Top 20 列表。请回复您打算重点关注的文献序号（例如：1,3,5-8），或者回复'全部'。收到指令后我将进入下一阶段的分析。"

---

## Phase 6: 基于摘要的智能聚合与分析

仅针对用户选中的文献执行以下分析（不涉及全文内容）：

1. **核心主题聚类**：根据摘要内容，将选中的论文自动划分为 2–4 个研究子主题（例如："基于深度学习的检测方法"、"传统统计模型的应用"）。
2. **研究趋势推断**：基于摘要中的高频关键词和时间线，总结该领域近期的研究热点变化。
3. **争议焦点识别**：分析不同文献摘要中提及的"limitation"、"future work"或"unsolved problem"，归纳当前领域共同面临的挑战。

输出：生成一份"聚类分析摘要"，包含主题群组、各群组代表文献及群组研究重点。

---

## Phase 7: 结构化报告生成 [Checkpoint]

将上述信息整合，生成最终的文献综述笔记。报告格式详见 `references/output_templates.md`。

### 格式要求

- **全局概述**：基于所有摘要，写一段 150 字左右的领域现状总述。
- **主题分组表格**：将文献按 Phase 6 的聚类分组，每组内按时间排序，列出"作者、年份、标题、DOI、核心贡献点（基于摘要提炼）"。
- **标准引用**：每篇文献附带 GB/T 7714 格式的引用。

### 输出与确认

暂停：生成报告后，询问用户："报告草稿已完成。是否需要调整分组逻辑，或修改引用格式（默认为 GB/T 7714）？"

---

## Phase 8: 输出格式选择与生成 [Checkpoint]

微调报告后，向用户询问输出格式，然后调用 `tools/output_report.py` 生成：

> 1. **Word 文档** (.docx)  — `python tools/output_report.py --input sorted.json --format word --topic "{topic}" --date "{date}"`
> 2. **Markdown 文档** (.md) — `python tools/output_report.py --input sorted.json --format markdown --topic "{topic}" --date "{date}"`
> 3. **Excel 摘要表** (.xlsx) — `python tools/output_report.py --input sorted.json --format excel --topic "{topic}" --date "{date}"`
> 4. **全部三种** — `python tools/output_report.py --input sorted.json --format all --topic "{topic}" --date "{date}"`

> Word/Markdown 可加 `--overview` 参数传入领域概述文本。三种输出格式的完整模板约定见 `references/output_templates.md`。
---

## 工具调用指南

| 工具名称 | 功能描述 | 输入 | 输出 |
|---|---|---|---|
| `tools/build_whitelist.py` | 根据用户条件从 CSV 分级表中构建期刊/会议白名单 | `filters.json`（含文献类型、分区、CCF 等级） | `journal_whitelist` + `conference_whitelist` + 统计摘要 |
| `tools/search_arxiv.py` | 调用 arXiv 官方 API 检索预印本，不应用白名单过滤 | `keywords`（关键词列表）, `max_results=30` | 20 篇 arXiv 文献（标题、作者、年份、DOI、摘要、PDF 链接） |
| `tools/search_openalex.py` | 调用 OpenAlex API 检索学术文献，应用白名单过滤（cursor 分页） | `keywords`（关键词列表）, `per_page=100`, `return_count=30`, `max_pages=5`, `journal_whitelist`, `conference_whitelist` | 30 篇符合白名单要求的文献（标题、作者、年份、DOI、摘要、期刊/会议、引用量） |
| `tools/merge_dedup.py` | 合并 arXiv 与 OpenAlex 文献并按 DOI/标题去重 | `--arxiv`（arXiv 结果）, `--openalex`（OpenAlex 结果） | 去重后的合并文献列表 + 统计信息 |
| `tools/backfill_tier.py` | 查询本地分级表为文献回填等级（中科院分区 / CCF 等级） | `papers.json`（合并后的文献列表） | 回填 `tier` 字段后的文献列表 + 统计信息 |
| `tools/sort_papers.py` | 按用户指定的标准（年份/引用量/等级）排序 | `papers`（文献列表）, `sort_by`（排序标准） | 排序后的文献列表 |

**异常处理**：若任一检索工具调用失败（如网络超时或 API 限制），需提示用户并继续使用其他可用库进行检索。

---

## 参考文件

- 匹配规则详见：`references/filter_rules.md`
- 报告模板详见：`references/output_templates.md`

---

## 免责声明

本工具提供的信息与分析仅基于公开的标题和摘要，不包含对论文全文的解读。最终研究结论请以论文 PDF 原稿为准。所有数据来源于 arXiv 和 OpenAlex 的公开 API，引用量、分区等信息仅供参考。
