"""
backfill_tier.py - 为文献列表回填等级信息（Phase 4 数据清洗）

根据 references/filter_rules.md 中的等级回填规则：
- OpenAlex 文献：用 venue 名称匹配中科院分区表和 CCF 分级表，回填 tier 字段
- arXiv 文献：无 venue，保持 tier=None

匹配策略：
- 中科院分区表：精确匹配 → 忽略大小写匹配（分区 1→"中科院一区" 等）
- CCF 分级表：全称精确匹配 → 简称精确匹配 → 忽略大小写匹配（分类 A→"CCF A 类"）
- 同时命中两个表时合并标注，如 "中科院一区 / CCF A 类"

用法:
    python tools/backfill_tier.py --input papers.json --output papers_tiered.json

输入 (papers.json): 文献数组（来自 search_openalex.py / search_arxiv.py 合并结果）
输出 (papers_tiered.json): 回填 tier 后的文献数组 + 统计信息
"""

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
REFERENCES_DIR = PROJECT_ROOT / "assets"

# 分区数字 → 中文标签
ZONE_LABEL = {1: "中科院一区", 2: "中科院二区", 3: "中科院三区", 4: "中科院四区"}


def load_cas_index() -> dict[str, str]:
    """加载中科院分区表，构建 venue(小写) → 等级标签 的索引。"""
    path = REFERENCES_DIR / "2025中科院分区表.csv"
    df = pd.read_excel(path, engine="openpyxl")
    index = {}
    for _, row in df.iterrows():
        name = row.get("期刊名称")
        zone = row.get("分区")
        if pd.notna(name) and pd.notna(zone):
            label = ZONE_LABEL.get(int(zone))
            if label:
                index[str(name).strip().lower()] = label
    return index


def load_ccf_index() -> dict[str, str]:
    """
    加载 CCF 分级表，构建 venue(小写) → 等级标签 的索引。
    全称和简称都建索引。
    """
    path = REFERENCES_DIR / "中国计算机学会国际学术会议分区.csv"
    df = pd.read_excel(path, engine="xlrd")
    index = {}
    for _, row in df.iterrows():
        category = row.get("分类")
        if not pd.notna(category):
            continue
        label = f"CCF {category} 类"
        # 全称
        full_name = row.get("全称")
        if pd.notna(full_name) and str(full_name).strip():
            index[str(full_name).strip().lower()] = label
        # 简称
        abbr = row.get("简称")
        if pd.notna(abbr) and str(abbr).strip():
            index[str(abbr).strip().lower()] = label
    return index


def match_tier(venue: str | None, cas_index: dict, ccf_index: dict) -> str | None:
    """根据 venue 匹配等级标签，返回合并后的 tier。"""
    if not venue:
        return None

    venue_lower = venue.strip().lower()
    cas_label = cas_index.get(venue_lower)
    ccf_label = ccf_index.get(venue_lower)

    if cas_label and ccf_label:
        return f"{cas_label} / {ccf_label}"
    return cas_label or ccf_label or None


def backfill(papers: list[dict]) -> tuple[list[dict], dict]:
    """为文献列表回填 tier 字段，返回 (新列表, 统计信息)。"""
    cas_index = load_cas_index()
    ccf_index = load_ccf_index()

    matched_count = 0
    for paper in papers:
        # arXiv 保底文献无 venue，跳过
        venue = paper.get("venue")
        if not venue:
            continue
        tier = match_tier(venue, cas_index, ccf_index)
        if tier:
            paper["tier"] = tier
            # 有等级信息的文献标记为合规
            paper["compliant"] = True
            matched_count += 1

    stats = {
        "total_papers": len(papers),
        "tier_matched": matched_count,
        "tier_unmatched": len(papers) - matched_count,
    }
    return papers, stats


def main():
    parser = argparse.ArgumentParser(description="为文献列表回填等级信息")
    parser.add_argument("--input", required=True, help="输入文献 JSON 文件路径")
    parser.add_argument("--output", default=None, help="输出文件路径（默认 stdout）")
    args = parser.parse_args()

    with open(args.input, "r", encoding="utf-8") as f:
        data = json.load(f)
    # 兼容 {papers:[...]} 包装格式和纯数组格式
    if isinstance(data, dict) and "papers" in data:
        papers = data["papers"]
    elif isinstance(data, list):
        papers = data
    else:
        print(f"[ERROR] 无法解析输入文件，期望文献数组或含 papers 字段的对象", file=sys.stderr)
        sys.exit(1)

    papers, stats = backfill(papers)

    result = {"stats": stats, "papers": papers}
    output_json = json.dumps(result, ensure_ascii=False, indent=2)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output_json)
        print(f"[INFO] 等级回填完成: {stats['tier_matched']}/{stats['total_papers']} 篇命中 → {args.output}", file=sys.stderr)
    else:
        print(output_json)


if __name__ == "__main__":
    main()
