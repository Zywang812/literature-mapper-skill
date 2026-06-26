"""
merge_dedup.py - 合并 arXiv 保底文献与 OpenAlex 精品文献并去重（Phase 3 第三层）

去重规则详见 references/filter_rules.md：
- 优先按 DOI 去重（非空且相同视为重复）
- DOI 为空时按标题精确匹配去重（忽略大小写和首尾空格）
- arXiv + OpenAlex 同时存在同一篇：保留 OpenAlex 版本（元数据更丰富），
  来源标记为 "arXiv & OpenAlex"，compliant 标记为 True

用法:
    python tools/merge_dedup.py \
        --arxiv arxiv_results.json \
        --openalex openalex_results.json \
        --output merged.json

输入: 两个文件均为 { ..., "papers": [...] } 结构（search_*.py 的输出）
输出: { "stats": {...}, "papers": [...] }
"""

import argparse
import json
import sys


def _normalize_doi(doi: str | None) -> str | None:
    """归一化 DOI：去前缀、转小写、去空格，无值返回 None。"""
    if not doi:
        return None
    doi = doi.replace("https://doi.org/", "").strip().lower()
    return doi or None


def _normalize_title(title: str | None) -> str | None:
    """归一化标题：去空格、转小写、折叠多余空白，无值返回 None。"""
    if not title:
        return None
    return " ".join(title.strip().lower().split()) or None


def _merge_fields(kept: dict, dropped: dict) -> dict:
    """
    合并两篇重复文献的字段：保留 kept 的主体，
    但 dropped（OpenAlex）有更丰富的元数据时覆盖缺失字段。
    """
    merged = dict(kept)
    for key in ("abstract", "venue", "cited_by_count", "doi", "authors", "year", "pdf_url"):
        # kept 缺失或为空时，用 dropped 补充
        if not merged.get(key) and dropped.get(key):
            merged[key] = dropped[key]
    return merged


def merge_dedup(arxiv_papers: list[dict], openalex_papers: list[dict]) -> tuple[list[dict], dict]:
    """
    合并两份文献列表并去重。

    策略：先建立 OpenAlex 文献的 DOI/标题索引，遍历 arXiv 文献时
    命中索引则合并（标记 Both），未命中则独立保留。
    """
    # 建立 OpenAlex 文献索引：key → 在 openalex_papers 中的位置
    openalex_by_doi: dict[str, int] = {}
    openalex_by_title: dict[str, int] = {}
    for i, p in enumerate(openalex_papers):
        doi = _normalize_doi(p.get("doi"))
        if doi:
            openalex_by_doi[doi] = i
        title = _normalize_title(p.get("title"))
        if title:
            openalex_by_title[title] = i

    result = list(openalex_papers)  # OpenAlex 精品文献全部保留
    both_count = 0
    arxiv_unique_count = 0

    for arxiv_paper in arxiv_papers:
        doi = _normalize_doi(arxiv_paper.get("doi"))
        title = _normalize_title(arxiv_paper.get("title"))

        # 优先按 DOI 匹配
        matched_idx = None
        if doi and doi in openalex_by_doi:
            matched_idx = openalex_by_doi[doi]
        # 退而按标题匹配
        elif title and title in openalex_by_title:
            matched_idx = openalex_by_title[title]

        if matched_idx is not None:
            # 命中：合并到 OpenAlex 版本，标记来源为 Both
            oa_paper = result[matched_idx]
            oa_paper = _merge_fields(oa_paper, arxiv_paper)
            oa_paper["source"] = "Both"
            oa_paper["compliant"] = True
            result[matched_idx] = oa_paper
            both_count += 1
        else:
            # 未命中：arXiv 文献独立保留
            result.append(arxiv_paper)
            arxiv_unique_count += 1

    stats = {
        "arxiv_input": len(arxiv_papers),
        "openalex_input": len(openalex_papers),
        "merged_both": both_count,
        "arxiv_unique": arxiv_unique_count,
        "total_after_dedup": len(result),
        "duplicates_removed": (len(arxiv_papers) + len(openalex_papers)) - len(result),
    }
    return result, stats


def _load_papers(path: str) -> list[dict]:
    """加载文件，兼容 {papers:[...]} 和 [...] 两种结构。"""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, dict) and "papers" in data:
        return data["papers"]
    if isinstance(data, list):
        return data
    raise ValueError(f"无法解析 {path}：期望文献数组或含 papers 字段的对象")


def main():
    parser = argparse.ArgumentParser(description="合并 arXiv 与 OpenAlex 文献并去重")
    parser.add_argument("--arxiv", required=True, help="arXiv 检索结果 JSON 路径")
    parser.add_argument("--openalex", required=True, help="OpenAlex 检索结果 JSON 路径")
    parser.add_argument("--output", default=None, help="输出文件路径（默认 stdout）")
    args = parser.parse_args()

    arxiv_papers = _load_papers(args.arxiv)
    openalex_papers = _load_papers(args.openalex)

    papers, stats = merge_dedup(arxiv_papers, openalex_papers)

    result = {"stats": stats, "papers": papers}
    output_json = json.dumps(result, ensure_ascii=False, indent=2)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output_json)
        print(
            f"[INFO] 合并去重完成: arXiv {stats['arxiv_input']} + OpenAlex {stats['openalex_input']}"
            f" → {stats['total_after_dedup']} 篇（重复 {stats['duplicates_removed']} 篇已剔除）→ {args.output}",
            file=sys.stderr,
        )
    else:
        print(output_json)


if __name__ == "__main__":
    main()
