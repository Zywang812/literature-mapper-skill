# 输出模板

本文档定义各阶段输出的标准格式模板。

---

## 1. Phase 5: Top 20 推荐列表

### 输出格式

```markdown
## Top 20 推荐文献

> 排序标准：{sort_by} | 精品文献优先排列

| 序号 | 标题 | 作者 | 年份 | 来源 | DOI | 引用量 | 符合等级 | 等级 |
|---|---|---|---|---|---|---|---|---|
| 1 | {title} | {authors} | {year} | {source} | {doi} | {citations} | {compliant} | {tier} |
| 2 | {title} | {authors} | {year} | {source} | {doi} | {citations} | {compliant} | {tier} |
| ... | ... | ... | ... | ... | ... | ... | ... | ... |
| 20 | {title} | {authors} | {year} | {source} | {doi} | {citations} | {compliant} | {tier} |

**统计**：共 {total_count} 篇文献，其中精品文献 {premium_count} 篇，保底文献 {baseline_count} 篇。
```

### 字段说明

| 字段 | 说明 |
|---|---|
| 序号 | 1–20 |
| 标题 | 文献标题 |
| 作者 | 前 3 位作者，超过用"等"省略 |
| 年份 | 发表年份 |
| 来源 | `arXiv` / `OpenAlex` / `Both` |
| DOI | DOI 编号，无则显示 `-` |
| 引用量 | 引用次数，无则显示 `-` |
| 符合等级 | `是` / `否` |
| 等级 | 如"中科院一区"、"CCF A 类"，无则显示 `-` |

---

## 2. Phase 6: 聚类分析摘要

### 输出格式

```markdown
## 聚类分析摘要

> 基于选中 {selected_count} 篇文献的摘要内容自动聚类

### 主题 1: {topic_name}

**研究重点**：{topic_summary}

**代表文献**：
- [{title}]({doi_url}) — {authors} ({year})：{key_contribution}

### 主题 2: {topic_name}

**研究重点**：{topic_summary}

**代表文献**：
- [{title}]({doi_url}) — {authors} ({year})：{key_contribution}

### 研究趋势

{trend_summary}

### 当前挑战与争议

{challenge_summary}
```

### 字段说明

| 字段 | 说明 |
|---|---|
| topic_name | 2–4 个字符的主题标签，如"深度学习检测方法" |
| topic_summary | 该主题下 50–100 字的概括 |
| title | 代表文献标题 |
| doi_url | DOI 链接，无 DOI 则链接到 arXiv abs 页 |
| authors | 第一作者 |
| year | 发表年份 |
| key_contribution | 基于摘要提炼的核心贡献，30–50 字 |
| trend_summary | 100–200 字的研究趋势总结 |
| challenge_summary | 100–200 字的挑战与争议总结 |

---

## 3. Phase 7: 最终文献综述报告

### 输出格式

```markdown
# {research_topic} 文献综述

> 检索时间：{date}
> 检索范围：{time_range}
> 数据来源：arXiv + OpenAlex
> 文献总数：{total_count} 篇

---

## 一、领域概述

{overview_150_words}

---

## 二、主题分组

### 2.1 {group_name}

{group_brief}

| 作者 | 年份 | 标题 | DOI | 核心贡献 |
|---|---|---|---|---|
| {authors} | {year} | {title} | [{doi}]({doi_url}) | {contribution} |
| {authors} | {year} | {title} | [{doi}]({doi_url}) | {contribution} |

### 2.2 {group_name}

{group_brief}

| 作者 | 年份 | 标题 | DOI | 核心贡献 |
|---|---|---|---|---|
| {authors} | {year} | {title} | [{doi}]({doi_url}) | {contribution} |
| {authors} | {year} | {title} | [{doi}]({doi_url}) | {contribution} |

---

## 三、参考文献

1. {authors}. {title}[{type}]. {venue}, {year}. DOI: {doi}
2. {authors}. {title}[{type}]. {venue}, {year}. DOI: {doi}
3. {authors}. {title}[{type}]. {venue}, {year}. DOI: {doi}
...
```

### 字段说明

| 字段 | 说明 |
|---|---|
| research_topic | 用户的研究主题关键词 |
| date | 报告生成日期，格式 YYYY-MM-DD |
| time_range | 用户指定的时间范围 |
| total_count | 选中的文献总数 |
| overview_150_words | 约 150 字的领域现状总述 |
| group_name | 主题分组名称 |
| group_brief | 该分组的 50–80 字概述 |
| contribution | 基于摘要提炼的核心贡献，30–50 字 |

### 引用格式（GB/T 7714）

参考文献条目采用 GB/T 7714 格式：

```
{authors}. {title}[J/{C}]. {venue}, {year}.
```

- 期刊论文类型标识：`[J]`
- 会议论文类型标识：`[C]`
- 有 DOI 时在末尾追加 `DOI: {doi}`
- 作者格式：前 3 位作者用逗号分隔，超过 3 位加", 等"
- arXiv 预印本 venue 标注为 `arXiv preprint`


---

## 4. Phase 8: 最终交付输出格式

`tools/output_report.py` 负责生成三种格式的输出，以下约定每种格式的标准结构。

---

### 4.1 Markdown 报告格式 (.md)

```markdown
# {research_topic} 文献综述

> 检索时间：{date}
> 数据来源：arXiv + OpenAlex
> 文献总数：{total} 篇（精品 {premium} 篇 / 保底 {baseline} 篇）

---

## 一、领域概述

{overview_text}

---

## 二、文献列表

| 序号 | 标题 | 作者 | 年份 | 来源 | DOI | 期刊/会议 | 引用量 | 符合等级 | 等级 |
|------|------|------|------|------|-----|-----------|--------|----------|------|
| 1 | {title} | {authors} | {year} | {source} | {doi} | {venue} | {citations} | {compliant} | {tier} |
| 2 | ... | ... | ... | ... | ... | ... | ... | ... | ... |

---

## 三、参考文献

1. {authors}. {title}[J/{C}]. {venue}, {year}. DOI: {doi}
2. ...
```

**字段说明：**
| 字段 | 说明 |
|---|---|
| research_topic | 用户的研究主题 |
| date | 报告日期，格式 YYYY-MM-DD |
| total / premium / baseline | 文献统计：总数 / 精品数 / 保底数 |
| overview_text | 约 150 字的领域现状总述 |
| title | 文献标题 |
| authors | 前 3 位作者，超过用"等"省略 |
| year | 发表年份 |
| source | arXiv / OpenAlex / Both |
| doi | DOI 编号，无则 - |
| venue | 期刊/会议名称，arXiv 标为"arXiv preprint" |
| citations | 引用次数，无则 - |
| compliant | 是 / 否 |
| tier | 如"中科院一区"或"CCF A 类"，无则 - |

---

### 4.2 Word 文档格式 (.docx)

使用 python-docx 生成，结构如下：

**页面结构：**
1. **封面页**：标题居中，下方附检索时间、数据来源、文献总数等元信息
2. **领域概述**：一级标题"一、领域概述"，正文段落概述
3. **文献列表**：一级标题"二、文献列表"，含 9 列表格（序号 / 标题 / 作者 / 年份 / 来源 / DOI / 期刊会议 / 引用量 / 等级）
4. **参考文献**：一级标题"三、参考文献"，编号列表，GB/T 7714 格式

**排版规则：**
- 表格使用 "Light Grid Accent 1" 样式
- 参考文献使用 List Number 样式自动编号
- 元信息用 10pt 灰色字体
- 所有中文字体默认使用文档默认字体

---

### 4.3 Excel 摘要表格式 (.xlsx)

使用 openpyxl 生成，单工作表"文献摘要"。

**列定义：**

| 列名 | 宽度 | 说明 |
|---|---|---|
| 序号 | 6 | 1-based 编号 |
| 标题 | 40 | 论文标题 |
| 作者 | 20 | 前 3 位作者 |
| 年份 | 8 | 发表年份 |
| 来源 | 12 | arXiv / OpenAlex / Both |
| DOI | 30 | DOI 链接 |
| 期刊/会议 | 25 | 发表出处 |
| 引用量 | 10 | 引用次数 |
| 等级 | 18 | 中科院分区 / CCF 等级 |
| 符合等级要求 | 12 | 是 / 否 |
| 摘要 | 60 | 论文摘要全文，自动换行 |

**排版规则：**
- 首行：蓝色背景（D9E1F2）加粗字体
- 所有行：带细边框
- 数据行：垂直顶部对齐，自动换行
- 摘要列最大宽度 60

---

### 参数速查

```bash
python tools/output_report.py --input <papers.json> --format <markdown|excel|word|all> --topic <string> --date <YYYY-MM-DD> --overview <text> --output-dir <path>
```
