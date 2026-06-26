"""
search_openalex.py - 调用 OpenAlex API 检索学术文献，应用白名单过滤

用法:
    python tools/search_openalex.py \
        --query "large language model medical diagnosis" \
        --journal-whitelist '["Nature","Science"]' \
        --conference-whitelist '["AAAI","CVPR"]' \
        --per-page 100 \
        --return-count 30

输入:
    --query              搜索关键词（空格分隔，OpenAlex 自动全文语义搜索）
    --journal-whitelist   期刊白名单 JSON 数组
    --conference-whitelist 会议白名单 JSON 数组
    --per-page           每页结果数（默认 100）
    --return-count       实际返回篇数（默认 30）
    --from-year          起始年份过滤（可选）
    --to-year            截止年份过滤（可选）
    --output             输出文件路径（可选，默认 stdout）

输出 (JSON):
{
    "query": "...",
    "total_fetched": 443456,
    "after_filter": 45,
    "returned": 30,
    "papers": [...]
}
"""

import argparse
import json
import sys

import requests

OPENALEX_API_BASE = "https://api.openalex.org/works"
# OpenAlex polite pool 速率控制（秒）
REQUEST_DELAY = 0.15


def reconstruct_abstract(inverted_index: dict) -> str:
    """
    将 OpenAlex 的倒排索引摘要还原为完整字符串。

    OpenAlex 返回的 abstract_inverted_index 格式为 {word: [positions]}，
    例如 {"Deep": [0], "learning": [1, 5], ...}。
    需要按位置重建原文。
    """
    if not inverted_index or not isinstance(inverted_index, dict):
        return ""
    # 构建位置 → 词 的映射
    position_to_word: dict[int, str] = {}
    for word, positions in inverted_index.items():
        for pos in positions:
            position_to_word[pos] = word
    if not position_to_word:
        return ""
    # 按位置顺序拼接
    max_pos = max(position_to_word.keys())
    words = [position_to_word.get(i, "") for i in range(max_pos + 1)]
    return " ".join(words)


def parse_work(work: dict) -> dict:
    """将 OpenAlex 返回的单条 work 记录解析为标准化文献格式。"""
    title = (work.get("title") or "").replace("\n", " ").strip()

    authors = []
    for authorship in work.get("authorships") or []:
        author_info = authorship.get("author") or {}
        name = author_info.get("display_name") or ""
        if name:
            authors.append(name)

    year = work.get("publication_year")

    doi = work.get("doi")
    if doi:
        doi = doi.replace("https://doi.org/", "").strip()

    abstract = reconstruct_abstract(work.get("abstract_inverted_index"))

    venue = None
    primary_location = work.get("primary_location") or {}
    source = primary_location.get("source") or {}
    venue = source.get("display_name")

    raw_type = work.get("type") or ""
    type_map = {
        "article": "Journal",
        "proceedings-article": "Conference",
        "conference-paper": "Conference",
        "book-chapter": "Book Chapter",
        "dissertation": "Thesis",
        "preprint": "Preprint",
        "dataset": "Dataset",
    }
    doc_type = type_map.get(raw_type, "Unknown")

    cited_by_count = work.get("cited_by_count")

    return {
        "title": title,
        "authors": authors,
        "year": year,
        "doi": doi,
        "abstract": abstract.replace("\n", " ").strip(),
        "venue": venue,
        "source": "OpenAlex",
        "compliant": True,
        "tier": None,
        "cited_by_count": cited_by_count,
        "type": doc_type,
    }


def match_venue(venue: str | None, whitelist_lower: set[str]) -> bool:
    """
    判断文献的 venue 是否在白名单中。

    采用双向包含匹配：白名单名称是 venue 的子串，或 venue 是白名单名称的子串。
    例如白名单中的 "ACM Computing Surveys" 能匹配 venue "ACM Computing Surveys"。
    """
    if not venue or not whitelist_lower:
        return not whitelist_lower  # 无白名单时全部通过
    venue_lower = venue.lower()
    for wl in whitelist_lower:
        if wl in venue_lower or venue_lower in wl:
            return True
    return False


def search_papers(
    query: str,
    journal_whitelist: list[str] | None = None,
    conference_whitelist: list[str] | None = None,
    per_page: int = 100,
    return_count: int = 30,
    from_year: int | None = None,
    to_year: int | None = None,
    max_pages: int = 5,
) -> dict:
    """
    调用 OpenAlex API 检索文献，使用 cursor 分页拉取。

    策略：API 端仅用 search + publication_year 过滤（避免 URL 编码问题），
    白名单匹配在本地完成。通过 cursor 分页最多拉取 max_pages 页，
    直到本地过滤后凑够 return_count 篇或达到页数上限。
    """
    import time

    journal_whitelist = journal_whitelist or []
    conference_whitelist = conference_whitelist or []

    full_whitelist_lower = {name.lower() for name in journal_whitelist + conference_whitelist}

    # 构建 filter 字符串（仅年份）
    filter_parts = []
    if from_year and to_year:
        filter_parts.append(f"publication_year:{from_year}-{to_year}")
    elif from_year:
        filter_parts.append(f"publication_year:>{from_year - 1}")
    elif to_year:
        filter_parts.append(f"publication_year:<{to_year + 1}")

    headers = {
        "User-Agent": "LiteratureMapper/1.0 (mailto:literature-mapper@local)",
    }

    all_papers = []
    total_api_results = 0
    seen_dois: set[str] = set()  # 防止分页间重复

    cursor = "*"
    for page in range(max_pages):
        params: dict = {
            "search": query,
            "per_page": min(per_page, 200),
            "mailto": "literature-mapper@local",
            "cursor": cursor,
        }
        if filter_parts:
            params["filter"] = "|".join(filter_parts)

        try:
            response = requests.get(
                OPENALEX_API_BASE,
                params=params,
                headers=headers,
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()
        except requests.exceptions.Timeout:
            print(f"[ERROR] OpenAlex API 第 {page + 1} 页请求超时", file=sys.stderr)
            break
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] OpenAlex API 第 {page + 1} 页请求失败: {e}", file=sys.stderr)
            break

        meta = data.get("meta", {})
        total_api_results = meta.get("count", 0)
        results = data.get("results") or []

        if not results:
            break  # 无更多结果

        for work in results:
            paper = parse_work(work)

            # 跳过已见过的 DOI（分页间可能有少量重复）
            doi = paper.get("doi")
            if doi and doi in seen_dois:
                continue
            if doi:
                seen_dois.add(doi)

            # 本地白名单过滤
            if not match_venue(paper.get("venue"), full_whitelist_lower):
                continue

            # 只保留有标题和摘要的文献
            if paper["title"] and paper["abstract"]:
                all_papers.append(paper)

        # 检查是否已凑够
        if len(all_papers) >= return_count:
            break

        # 获取下一页 cursor
        next_cursor = meta.get("next_cursor")
        if not next_cursor:
            break  # 没有更多页
        cursor = next_cursor

        # 速率控制：polite pool 建议 10 次/秒
        time.sleep(REQUEST_DELAY)

    # 按引用量降序排序后取前 return_count 篇
    all_papers.sort(key=lambda p: p.get("cited_by_count") or 0, reverse=True)
    returned_papers = all_papers[:return_count]

    return {
        "query": query,
        "total_fetched": total_api_results,
        "after_filter": len(all_papers),
        "returned": len(returned_papers),
        "papers": returned_papers,
    }


def main():
    parser = argparse.ArgumentParser(description="检索 OpenAlex 学术文献（应用白名单过滤）")
    parser.add_argument("--query", required=True, help="搜索关键词")
    parser.add_argument("--journal-whitelist", default="[]", help="期刊白名单 JSON 数组")
    parser.add_argument("--conference-whitelist", default="[]", help="会议白名单 JSON 数组")
    parser.add_argument("--per-page", type=int, default=100, help="每页结果数（默认 100）")
    parser.add_argument("--return-count", type=int, default=30, help="实际返回篇数（默认 30）")
    parser.add_argument("--from-year", type=int, default=None, help="起始年份")
    parser.add_argument("--to-year", type=int, default=None, help="截止年份")
    parser.add_argument("--output", default=None, help="输出文件路径（默认 stdout）")
    parser.add_argument("--max-pages", type=int, default=5, help="最大分页数（默认 5）")
    args = parser.parse_args()

    journal_whitelist = json.loads(args.journal_whitelist)
    conference_whitelist = json.loads(args.conference_whitelist)

    result = search_papers(
        query=args.query,
        journal_whitelist=journal_whitelist,
        conference_whitelist=conference_whitelist,
        per_page=args.per_page,
        return_count=args.return_count,
        from_year=args.from_year,
        to_year=args.to_year,
        max_pages=args.max_pages,
    )

    output_json = json.dumps(result, ensure_ascii=False, indent=2)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output_json)
        print(f"[INFO] 已写入 {args.output}", file=sys.stderr)
    else:
        print(output_json)


if __name__ == "__main__":
    main()
