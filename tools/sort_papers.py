"""
sort_papers.py - 按用户指定标准对文献列表排序

排序规则详见 references/filter_rules.md：
- 合规优先：符合等级要求的文献始终排在其他文献之前
- 三种排序标准：year（年份降序）/ citations（引用量降序）/ tier（等级降序）
- 同组内 null 值排在末尾

用法:
    python tools/sort_papers.py --input papers.json --sort-by citations --output sorted.json

输入 (papers.json): 文献数组，每篇含 year/cited_by_count/tier/compliant 等字段
输出 (sorted.json): 排序后的文献数组
"""

import argparse
import json
import sys

# 等级 → 权重映射（值越大排越前），详见 references/filter_rules.md
TIER_WEIGHT = {
    "中科院一区": 4,
    "中科院二区": 3,
    "中科院三区": 2,
    "中科院四区": 1,
    "CCF A 类": 4,
    "CCF B 类": 3,
    "CCF C 类": 2,
    "未收录": 0,
    "Unknown": 0,
}


def tier_weight(tier: str | None) -> int:
    """
    计算文献等级权重。

    tier 可能是单个等级（如"中科院一区"）或双标注（如"中科院一区 / CCF A 类"），
    取其中最高的权重。
    """
    if not tier:
        return 0
    # 处理双标注情况（用 / 分隔）
    parts = [p.strip() for p in tier.split("/")]
    weights = [TIER_WEIGHT.get(p, 0) for p in parts]
    return max(weights) if weights else 0


def year_key(paper: dict):
    """年份降序：null/None 排最后（用 -inf 实现）。"""
    year = paper.get("year")
    if year is None or year == "N/A":
        return (0, float("-inf"))
    try:
        return (1, int(year))
    except (TypeError, ValueError):
        return (0, float("-inf"))


def citation_key(paper: dict):
    """引用量降序：null 排最后。同引用量按年份降序作二级排序。"""
    citations = paper.get("cited_by_count")
    if citations is None:
        return (0, float("-inf"), float("-inf"))
    y = paper.get("year") or 0
    try:
        return (1, int(citations), int(y) if y and y != "N/A" else 0)
    except (TypeError, ValueError):
        return (0, float("-inf"), float("-inf"))


def tier_key(paper: dict):
    """等级降序：null 排最后。同等级按引用量降序作二级排序。"""
    t = paper.get("tier")
    if not t:
        return (0, 0, float("-inf"))
    w = tier_weight(t)
    citations = paper.get("cited_by_count") or 0
    try:
        return (1, w, int(citations))
    except (TypeError, ValueError):
        return (1, w, 0)


def sort_papers(papers: list[dict], sort_by: str) -> list[dict]:
    """
    对文献列表排序。

    核心原则：先按合规性分组（符合等级要求的在前、其他的在后），
    各组内再按用户指定标准排序。

    Args:
        papers: 文献列表
        sort_by: 排序标准 ("year" / "citations" / "tier")

    Returns:
        排序后的文献列表
    """
    # 选择排序键函数
    key_map = {
        "year": year_key,
        "citations": citation_key,
        "tier": tier_key,
    }
    if sort_by not in key_map:
        raise ValueError(f"不支持的排序标准: {sort_by}（可选: year/citations/tier）")
    key_fn = key_map[sort_by]

    # 符合等级要求优先：compliant=True 在前，False 在后
    # 各组内按用户指定标准降序排序，再拼接
    compliant_papers = [p for p in papers if p.get("compliant")]
    others = [p for p in papers if not p.get("compliant")]

    # 各组内按指定标准降序
    compliant_papers.sort(key=key_fn, reverse=True)
    others.sort(key=key_fn, reverse=True)

    return compliant_papers + others


def main():
    parser = argparse.ArgumentParser(description="对文献列表排序")
    parser.add_argument("--input", required=True, help="输入文献 JSON 文件路径")
    parser.add_argument("--sort-by", required=True, choices=["year", "citations", "tier"],
                        help="排序标准：year(年份) / citations(引用量) / tier(等级)")
    parser.add_argument("--output", default=None, help="输出文件路径（默认 stdout）")
    parser.add_argument("--top", type=int, default=None, help="只返回前 N 篇（可选）")
    args = parser.parse_args()

    with open(args.input, "r", encoding="utf-8") as f:
        data = json.load(f)
    # 兼容 {"papers":[...]} 包装格式和纯数组格式
    if isinstance(data, dict) and "papers" in data:
        papers = data["papers"]
    elif isinstance(data, list):
        papers = data
    else:
        print(f"[ERROR] 无法解析输入文件，期望论文数组或含 papers 字段的对象", file=sys.stderr)
        sys.exit(1)
    sorted_papers = sort_papers(papers, args.sort_by)

    if args.top:
        sorted_papers = sorted_papers[:args.top]

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(sorted_papers, f, ensure_ascii=False, indent=2)
        print(f"[INFO] 已写入 {args.output}", file=sys.stderr)
    else:
        print(json.dumps(sorted_papers, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
