#!/usr/bin/env python3
"""Collect public TikTok Creative Center jewelry candidates.

The collector intentionally uses only the public Creative Center API. It does
not log in, download media, or attempt to bypass regional or anti-bot controls.
Signed media URLs returned by TikTok are short-lived and are included only as
preview links in the generated report.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parent
API_BASE = "https://ads.tiktok.com/creative_radar_api/v1"
LIST_ENDPOINT = f"{API_BASE}/top_ads/v2/list"
FILTER_ENDPOINT = f"{API_BASE}/top_ads/v2/filters"
SOURCE_PAGE = "https://ads.tiktok.com/business/creativecenter/inspiration/topads/pc/en"
DEFAULT_COUNTRIES = ("US", "GB", "CA", "AU")
TARGET_INDUSTRIES = {
    "22106000000": "Ordinary Jewelry",
    "22107000000": "High-end Jewelry",
    "22101000000": "Clothing Accessories",
    "22000000000": "Apparel & Accessories",
}

DIY_RE = re.compile(
    r"\b(?:diy|do[ -]?it[ -]?yourself|bead(?:s|ed)?|charm(?:s)?|jewelry making|"
    r"handmade|craft(?:s|ing)?|wire[- ]?wrap|polymer clay|supplies)\b",
    re.I,
)
FINISHED_RE = re.compile(
    r"\b(?:jewelry|jewellery|necklace|bracelet|earrings?|ring(?:s)?|pendant|"
    r"anklet|brooch|bangle|watch(?:es)?|accessor(?:y|ies)|sunglasses|hair clip)\b",
    re.I,
)
PERSONA_RE = re.compile(
    r"\b(?:i|my|me|we|our|unboxing|grwm|review|styling|designer|founder|"
    r"story|recommend|try[- ]?on|haul|collection|lookbook|wearing)\b",
    re.I,
)


def fetch_json(url: str) -> dict[str, Any]:
    request = Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "George-public-creative-center-collector/1.0",
            "anonymous-user-id": "fake-user-id",
            "lang": "en",
        },
    )
    with urlopen(request, timeout=30) as response:
        return json.load(response)


def classify(material: dict[str, Any], industry_name: str) -> list[str]:
    text = " ".join(
        str(material.get(key) or "")
        for key in ("ad_title", "brand_name", "industry_key")
    )
    categories: list[str] = []
    if DIY_RE.search(text):
        categories.append("DIY 配件")
    if FINISHED_RE.search(text) or "Jewelry" in industry_name:
        categories.append("成品饰品")
    if PERSONA_RE.search(text):
        categories.append("人设口播")
    if not categories and "Accessory" in industry_name:
        categories.append("成品饰品")
    return categories


def material_record(
    material: dict[str, Any], country: str, industry_name: str
) -> dict[str, Any]:
    info = material.get("video_info") or {}
    urls = info.get("video_url") or {}
    preview = urls.get("1080p") or urls.get("720p") or urls.get("540p") or ""
    return {
        "material_id": str(material.get("id") or ""),
        "video_id": info.get("vid") or "",
        "categories": classify(material, industry_name),
        "country_filter": country,
        "industry": industry_name,
        "title": material.get("ad_title") or "",
        "brand": material.get("brand_name") or "",
        "like": material.get("like"),
        "ctr": material.get("ctr"),
        "cost": material.get("cost"),
        "duration_seconds": info.get("duration"),
        "width": info.get("width"),
        "height": info.get("height"),
        "cover_url": info.get("cover") or "",
        "preview_url": preview,
        "source_page": SOURCE_PAGE,
        "verification": "Creative Center public API response",
        "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
    }


def collect(countries: tuple[str, ...], limit: int = 20) -> dict[str, Any]:
    filters = fetch_json(FILTER_ENDPOINT)
    available = {
        str(item.get("id")): item.get("value")
        for item in (filters.get("data", {}).get("industry") or [])
    }
    selected = {
        key: available.get(key, value)
        for key, value in TARGET_INDUSTRIES.items()
        if key in available or key in TARGET_INDUSTRIES
    }

    records: dict[str, dict[str, Any]] = {}
    requests_made = 0
    errors: list[str] = []
    for country in countries:
        for industry_id, industry_name in selected.items():
            query = urlencode(
                {
                    "order_by": "impression",
                    "period": 30,
                    "country_code": country,
                    "industry": industry_id,
                    "keyword": "",
                    "page": 1,
                    "limit": limit,
                }
            )
            try:
                payload = fetch_json(f"{LIST_ENDPOINT}?{query}")
                requests_made += 1
            except Exception as exc:  # Keep other regions usable if one fails.
                errors.append(f"{country}/{industry_name}: {exc}")
                continue
            for material in payload.get("data", {}).get("materials") or []:
                record = material_record(material, country, industry_name)
                material_id = record["material_id"]
                if material_id:
                    records.setdefault(material_id, record)

    items = list(records.values())
    items.sort(key=lambda item: (-(item.get("like") or 0), -(item.get("ctr") or 0)))
    counts = {
        category: sum(category in item["categories"] for item in items)
        for category in ("DIY 配件", "成品饰品", "人设口播")
    }
    return {
        "retrieved_on": date.today().isoformat(),
        "period_days": 30,
        "market": list(countries),
        "source": SOURCE_PAGE,
        "api_endpoint": LIST_ENDPOINT,
        "requests_succeeded": requests_made,
        "items": items,
        "category_counts": counts,
        "limitations": [
            "Creative Center returned public ad-material metadata, not a universal TikTok organic-video ranking.",
            "Like and CTR are the values returned by the API; impressions and comments were not exposed in this response.",
            "preview_url and cover_url are signed TikTok CDN URLs and may expire.",
            "No media files were downloaded or committed.",
            "DIY is assigned only when the public title or brand text contains an explicit DIY/craft signal.",
        ],
        "errors": errors,
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# TikTok 饰品类公开候选采集报告",
        "",
        f"- 采集日期：{report['retrieved_on']}",
        f"- 时间范围：近 {report['period_days']} 天",
        f"- 市场筛选：{', '.join(report['market'])}",
        f"- 成功请求：{report['requests_succeeded']}",
        f"- 去重后素材：{len(report['items'])}",
        "- 来源：TikTok Creative Center 公开接口",
        "",
        "## 分类结果",
        "",
    ]
    for category, count in report["category_counts"].items():
        lines.append(f"- {category}：{count} 条")
    lines += [
        "",
        "> 说明：这里的“候选”是 Creative Center 广告素材列表中的公开样本，不等同于 TikTok 全站自然流量爆款。指标只引用接口实际返回值。",
        "",
        "## 素材清单",
        "",
    ]
    if not report["items"]:
        lines.append("本次接口未返回可用素材。")
    for index, item in enumerate(report["items"], 1):
        categories = "、".join(item["categories"]) or "未归类"
        lines += [
            f"### {index}. {item['title'] or '(无标题)'}",
            "",
            f"- 分类：{categories}",
            f"- 素材 ID：`{item['material_id']}`",
            f"- 视频 ID：`{item['video_id']}`",
            f"- 品牌：{item['brand'] or '未提供'}",
            f"- 行业：{item['industry']}",
            f"- 市场筛选：{item['country_filter']}",
            f"- API 点赞：{item['like'] if item['like'] is not None else '未提供'}",
            f"- API CTR：{item['ctr'] if item['ctr'] is not None else '未提供'}",
            f"- 时长：{item['duration_seconds'] if item['duration_seconds'] is not None else '未提供'} 秒",
            f"- 封面预览：[打开封面]({item['cover_url']})" if item["cover_url"] else "- 封面预览：未提供",
            f"- 视频预览：[打开时效链接]({item['preview_url']})" if item["preview_url"] else "- 视频预览：未提供",
            f"- 校验状态：{item['verification']}",
            "",
        ]
    lines += ["## 限制", ""]
    lines.extend(f"- {item}" for item in report["limitations"])
    if report["errors"]:
        lines += ["", "## 请求异常", ""]
        lines.extend(f"- {item}" for item in report["errors"])
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--countries", nargs="+", default=list(DEFAULT_COUNTRIES))
    args = parser.parse_args()
    output_dir = args.output_dir or ROOT / "output" / f"tiktok-jewelry-{date.today().isoformat()}"
    output_dir.mkdir(parents=True, exist_ok=True)
    report = collect(tuple(args.countries))
    (output_dir / "候选视频.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (output_dir / "候选视频.md").write_text(render_markdown(report), encoding="utf-8")
    print(json.dumps({"output_dir": str(output_dir), "category_counts": report["category_counts"], "items": len(report["items"])}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
