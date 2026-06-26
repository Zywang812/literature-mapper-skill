"""
build_whitelist.py - 根据用户条件从分级表中构建期刊/会议白名单

用法:
    python tools/build_whitelist.py --filters filters.json

输入 (filters.json):
{
    "document_type": "Both",        // "Journal" / "Conference" / "Both"
    "journal_level": "一区",         // "一区"/"二区"/"三区"/"四区"/"不限"
    "conference_level": "A",         // "A"/"B"/"C"/"不限"
}

输出 (stdout):
{
    "journal_whitelist": ["Nature", "Science", ...],
    "conference_whitelist": ["AAAI", "CVPR", ...],
    "stats": {
        "journal_from_cas": 5,
        "journal_from_ccf": 3,
        "journal_total": 7,
        "conference_total": 10
    }
}
"""

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

# 项目根目录（本文件在 tools/ 下）
PROJECT_ROOT = Path(__file__).resolve().parent.parent
REFERENCES_DIR = PROJECT_ROOT / "assets"

# 分区映射：中文 → 数字
ZONE_MAP = {
    "一区": 1,
    "二区": 2,
    "三区": 3,
    "四区": 4,
}


def load_cas_table() -> pd.DataFrame:
    """加载中科院分区表（实际为 .xlsx 格式，但扩展名为 .csv）"""
    path = REFERENCES_DIR / "2025中科院分区表.csv"
    return pd.read_excel(path, engine="openpyxl")


def load_ccf_table() -> pd.DataFrame:
    """加载 CCF 分区表（实际为 .xls 格式，但扩展名为 .csv）"""
    path = REFERENCES_DIR / "中国计算机学会国际学术会议分区.csv"
    return pd.read_excel(path, engine="xlrd")


def build_journal_whitelist(filters: dict) -> tuple[list[str], dict]:
    """
    构建期刊白名单，来源：
    1. 中科院分区表（按分区筛选）
    2. CCF 分区表中类型为"期刊"的记录
    """
    cas_df = load_cas_table()
    ccf_df = load_ccf_table()

    whitelist = set()
    cas_count = 0
    ccf_count = 0

    # 从中科院分区表筛选
    journal_level = filters.get("journal_level", "不限")
    if journal_level != "不限":
        target_zone = ZONE_MAP.get(journal_level)
        if target_zone is not None:
            filtered = cas_df[cas_df["分区"] <= target_zone]
            for name in filtered["期刊名称"].dropna().unique():
                whitelist.add(str(name).strip())
            cas_count = len(filtered)
    else:
        # 不限分区 → 全部加入
        for name in cas_df["期刊名称"].dropna().unique():
            whitelist.add(str(name).strip())
        cas_count = len(cas_df)

    # 从 CCF 分区表筛选类型为"期刊"的记录
    ccf_level = filters.get("conference_level", "不限")

    ccf_journals = ccf_df[ccf_df["类型"] == "期刊"]

    if ccf_level != "不限":
        ccf_journals = ccf_journals[ccf_journals["分类"] == ccf_level]



    for _, row in ccf_journals.iterrows():
        name = row["全称"] if pd.notna(row["全称"]) and str(row["全称"]).strip() else row["简称"]
        if pd.notna(name):
            whitelist.add(str(name).strip())
            ccf_count += 1

    return sorted(whitelist), {"cas_count": cas_count, "ccf_count": ccf_count, "total": len(whitelist)}


def build_conference_whitelist(filters: dict) -> tuple[list[str], int]:
    """
    构建会议白名单，来源：CCF 分区表中类型为"会议"的记录
    """
    ccf_df = load_ccf_table()

    ccf_level = filters.get("conference_level", "不限")

    ccf_conferences = ccf_df[ccf_df["类型"] == "会议"]

    if ccf_level != "不限":
        ccf_conferences = ccf_conferences[ccf_conferences["分类"] == ccf_level]



    whitelist = []
    for _, row in ccf_conferences.iterrows():
        # 优先用简称匹配（API 搜索时简称更常用），同时保留全称
        name = str(row["简称"]).strip() if pd.notna(row["简称"]) else None
        if name:
            whitelist.append(name)

    return sorted(set(whitelist)), len(whitelist)


def main():
    parser = argparse.ArgumentParser(description="构建期刊/会议白名单")
    parser.add_argument("--filters", required=True, help="筛选条件 JSON 文件路径")
    args = parser.parse_args()

    # 读取筛选条件
    with open(args.filters, "r", encoding="utf-8") as f:
        filters = json.load(f)

    document_type = filters.get("document_type", "Both")

    result = {
        "journal_whitelist": [],
        "conference_whitelist": [],
        "stats": {},
    }

    # 构建期刊白名单
    if document_type in ("Journal", "Both"):
        journal_list, journal_stats = build_journal_whitelist(filters)
        result["journal_whitelist"] = journal_list
        result["stats"]["journal_from_cas"] = journal_stats["cas_count"]
        result["stats"]["journal_from_ccf"] = journal_stats["ccf_count"]
        result["stats"]["journal_total"] = journal_stats["total"]

    # 构建会议白名单
    if document_type in ("Conference", "Both"):
        conference_list, conference_count = build_conference_whitelist(filters)
        result["conference_whitelist"] = conference_list
        result["stats"]["conference_total"] = conference_count

    # 输出 JSON
    json.dump(result, sys.stdout, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
