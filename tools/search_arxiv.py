"""
search_arxiv.py - 调用 arXiv API 检索预印本文献

用法:
    python tools/search_arxiv.py --query "large language model AND medical diagnosis" --max-results 30

输入:
    --query    arXiv 检索式，支持 ti: 和 abs: 前缀
    --max-results  抓取上限（默认 30）
    --output   输出文件路径（可选，默认 stdout）

输出 (JSON):
{
    "query": "...",
    "total_fetched": 30,
    "returned": 20,
    "papers": [
        {
            "title": "...",
            "authors": ["Author1", "Author2"],
            "year": 2024,
            "doi": "10.xxxx/xxxx",
            "abstract": "...",
            "pdf_url": "https://arxiv.org/pdf/xxxx",
            "source": "arXiv",
            "compliant": false,
            "tier": null,
            "cited_by_count": null,
            "type": "Unknown"
        },
        ...
    ]
}
"""

import argparse
import json
import sys
import time
from datetime import datetime

import arxiv


def search_papers(query: str, max_results: int = 30, return_count: int = 20) -> list[dict]:
    """
    调用 arXiv API 检索文献。

    Args:
        query: arXiv 检索式（支持 ti: 和 abs: 前缀）
        max_results: API 抓取上限
        return_count: 实际返回数量（按相关性排序后截取）

    Returns:
        标准化的文献列表
    """
    client = arxiv.Client(
        page_size=min(max_results, 100),
        delay_seconds=3.0,  # arXiv 要求请求间隔至少 3 秒
        num_retries=3,
    )

    search = arxiv.Search(
        query=query,
        max_results=max_results,
        sort_by=arxiv.SortCriterion.Relevance,
    )

    papers = []
    try:
        results = client.results(search)
    except Exception as e:
        print(f"[ERROR] arXiv API 请求失败: {e}", file=sys.stderr)
        return papers

    for result in results:
        # 解析发表年份
        year = None
        if result.published:
            year = result.published.year

        # 解析 DOI（arXiv 条目可能有也可能没有 DOI）
        doi = None
        if result.doi:
            doi = result.doi.strip()

        # 解析作者列表
        authors = [str(a) for a in result.authors]

        paper = {
            "title": result.title.replace("\n", " ").strip(),
            "authors": authors,
            "year": year,
            "doi": doi,
            "abstract": result.summary.replace("\n", " ").strip() if result.summary else "",
            "pdf_url": str(result.pdf_url) if result.pdf_url else None,
            "source": "arXiv",
            "compliant": False,  # arXiv 保底文献默认不符合等级要求
            "tier": None,
            "cited_by_count": None,
            "type": "Unknown",
        }
        papers.append(paper)

    # 按相关性排序后取前 return_count 篇
    # arxiv 包默认已按相关性排序，直接截取
    return papers[:return_count]


def main():
    parser = argparse.ArgumentParser(description="检索 arXiv 预印本文献")
    parser.add_argument("--query", required=True, help="arXiv 检索式")
    parser.add_argument("--max-results", type=int, default=30, help="API 抓取上限（默认 30）")
    parser.add_argument("--return-count", type=int, default=20, help="实际返回篇数（默认 20）")
    parser.add_argument("--output", default=None, help="输出文件路径（默认 stdout）")
    args = parser.parse_args()

    papers = search_papers(
        query=args.query,
        max_results=args.max_results,
        return_count=args.return_count,
    )

    result = {
        "query": args.query,
        "total_fetched": args.max_results,
        "returned": len(papers),
        "papers": papers,
    }

    output_json = json.dumps(result, ensure_ascii=False, indent=2)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output_json)
        print(f"[INFO] 已写入 {args.output}", file=sys.stderr)
    else:
        print(output_json)


if __name__ == "__main__":
    main()
