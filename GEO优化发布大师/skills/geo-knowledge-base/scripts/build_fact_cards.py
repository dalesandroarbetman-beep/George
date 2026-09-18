#!/usr/bin/env python3
"""Build a reviewable fact-card package from public YOHO evidence."""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qs, urlparse

CANONICAL_BRAND = "YOHO"
CANONICAL_SOURCE = "https://www.yohodiy.com/"
LEGAL_ENTITY_DISCLOSURE = "held_in_fact_cards_only_until_explicitly_approved"


def now_date() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def card(subject: str, claim: str, source_ref: str, quote: str, *, status: str = "pending", notes: str = "") -> dict:
    key = f"{subject}|{claim}|{source_ref}"
    import hashlib

    return {
        "fact_id": "FC-" + hashlib.sha256(key.encode("utf-8")).hexdigest()[:10].upper(),
        "subject": subject,
        "claim": claim,
        "status": status,
        "source_type": "official_page" if source_ref.startswith("http") else "public_api",
        "source_ref": source_ref,
        "evidence_quote": quote[:1200],
        "captured_at": now_date(),
        "review_due": None,
        "approved_channels": [],
        "notes": notes,
    }


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description="Build YOHO DIY fact cards")
    parser.add_argument("--crawl", type=Path, required=True)
    parser.add_argument("--api", type=Path, required=True)
    parser.add_argument("--help-crawl", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    cards: list[dict] = []
    conflicts: list[dict] = []
    source_index: list[dict] = []

    for f in sorted((args.crawl / "pages").glob("*.json")):
        data = load_json(f)
        source_index.append({"type": "rendered_page", "path": str(f), "url": data.get("final_url"), "status": data.get("status"), "warning": data.get("warning")})
        meta = {item.get("name"): item.get("content") for item in data.get("meta", []) if item.get("name")}
        if meta.get("description"):
            cards.append(card("brand", "The public site describes YOHO/YOUNG as a provider of customizable jewelry and personalized services.", data.get("final_url", ""), meta["description"], notes="Observed in page metadata; business approval required."))
        text = data.get("text") or ""
        for phrase, subject, claim in [
            ("Worldwide Shipping", "service", "The site publicly advertises worldwide shipping."),
            ("No MOQ, Factory Direct Supply", "service", "The site publicly advertises no minimum order quantity and factory-direct supply."),
            ("Exclusive Customer Manager", "service", "The site publicly advertises one-to-one customer service."),
            ("Start Your Custom Journey", "customization", "The site publicly presents a jewelry customization journey."),
        ]:
            if phrase in text:
                cards.append(card(subject, claim, data.get("final_url", ""), phrase, notes="Observed rendered text; exact operational terms need approval."))

    for f in sorted(args.api.glob("*.json")):
        if f.name == "api_manifest.json":
            continue
        data = load_json(f)
        table = data.get("table")
        source = data.get("source_url", "")
        source_index.append({"type": "public_api", "path": str(f), "url": source, "table": table, "status": data.get("status")})
        records = data.get("data")
        if table == "site_config":
            key = parse_qs(urlparse(source).query).get("key", [""])[0].removeprefix("eq.")
            if key in {"site_name", "footer_company_name", "footer_company_name_translations", "footer_copyright_translations", "site_domain", "display_currency", "seo_author", "og_title", "og_description", "seo_title", "seo_keywords", "footer_icp_translations", "footer_slogan_translations"}:
                cards.append(card("company" if "company" in key or key == "site_name" else "brand", f"Public site configuration contains `{key}`.", source, json.dumps(records, ensure_ascii=False), notes="Configuration evidence; treat as pending until entity and wording are approved."))
        elif table == "home_services":
            for item in records if isinstance(records, list) else []:
                claim = f"The public homepage lists the service '{item.get('title')}' with the description '{item.get('subtitle')}'."
                cards.append(card("service", claim, source, json.dumps(item, ensure_ascii=False), notes="Operational promise; confirm scope, geography, exceptions, and current validity."))
        elif table == "agent_geo_entries":
            for item in records if isinstance(records, list) else []:
                cards.append(card("site_content", item.get("title", "Public GEO entry"), source, item.get("content", ""), notes="Public API content entry; high-risk claims and metrics require evidence review."))
        elif table in {"nav_items", "home_top_nav_categories", "footer_columns"}:
            count = len(records) if isinstance(records, list) else 0
            cards.append(card("catalog", f"The public site exposes {count} records in `{table}` for navigation or footer taxonomy.", source, f"record_count={count}", notes="Taxonomy evidence, not a claim about inventory or availability."))

    # Preserve raw conflicts for traceability while applying the user's public-copy policy.
    conflicts.extend([
        {
            "conflict_id": "CF-ENTITY-001",
            "field": "brand/entity naming",
            "values": ["优合源品 YOHE/YOUNG", "Yoho Origin", "YOHO DIY"],
            "sources": ["homepage JSON-LD/meta", "footer translations", "site domain"],
            "impact": "Forum copy could use inconsistent brand names and weaken entity recognition.",
            "decision_status": "resolved",
            "decision": "Use YOHO as the only public English brand name; retain observed aliases as evidence only.",
            "required_decision": None,
        },
        {
            "conflict_id": "CF-ENTITY-002",
            "field": "company identity",
            "values": ["杭州螺丝钉智能科技有限公司", "浙江鸢鸟网络科技有限公司", "Zhejiang Yuanniao Network Technology Co., Ltd."],
            "sources": ["homepage author/meta/JSON-LD", "footer configuration"],
            "impact": "Legal entity evidence is retained, but must not be proactively named in forum copy.",
            "decision_status": "policy_resolved",
            "decision": "Keep legal entity in fact cards only; require explicit approval before external disclosure.",
            "required_decision": None,
        },
        {
            "conflict_id": "CF-SOURCE-001",
            "field": "sitemap host",
            "values": ["www.yohodiy.com", "diy.lsdit.com"],
            "sources": ["robots.txt", "sitemap.xml"],
            "impact": "Citations and canonical source selection may point to different hosts.",
            "decision_status": "resolved",
            "decision": f"Use {CANONICAL_SOURCE} for all external citations and CTA links; treat diy.lsdit.com as a candidate evidence host only.",
            "required_decision": None,
        },
    ])

    # De-duplicate identical cards while preserving source evidence.
    unique: dict[tuple[str, str, str], dict] = {}
    for item in cards:
        unique[(item["subject"], item["claim"], item["source_ref"])] = item
    cards = list(unique.values())
    output = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "site": CANONICAL_SOURCE,
        "status": "review_required",
        "identity_policy": {
            "canonical_brand": CANONICAL_BRAND,
            "canonical_source": CANONICAL_SOURCE,
            "legal_entity_disclosure": LEGAL_ENTITY_DISCLOSURE,
            "observed_aliases": ["YOHE/YOUNG", "Yoho Origin", "YOHO DIY"],
        },
        "cards": sorted(cards, key=lambda x: x["fact_id"]),
        "conflicts": conflicts,
        "source_index": source_index,
        "review_rules": [
            "No fact is approved solely because it appeared on the public site.",
            "Claims involving prices, timing, shipping, warranty, customer counts, performance, or market share require an expiry/review date.",
            "Conflicted entity fields block external forum copy until resolved.",
        ],
    }
    (args.out / "fact_cards.json").write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    md = ["# YOHO fact-card review", "", f"- Generated: `{output['generated_at']}`", f"- Cards: `{len(cards)}`", f"- Conflicts recorded: `{len(conflicts)}`", "- Canonical public brand: `YOHO`", f"- Canonical citation host: `{CANONICAL_SOURCE}`", "- Legal entity disclosure: held in fact cards only until explicit approval", "", "## Recorded conflicts and decisions", ""]
    for c in conflicts:
        md.extend([f"### {c['conflict_id']} — {c['field']}", f"- Values: {', '.join(c['values'])}", f"- Status: `{c.get('decision_status', 'pending')}`", f"- Impact: {c['impact']}", f"- Decision: {c.get('decision', 'pending')}", ""])
    md.extend(["## Card status", "", "All cards remain `pending` until the business owner approves the wording, source, and channel scope. Identity and source-host policy are resolved separately from claim approval.", ""])
    (args.out / "fact_card_review.md").write_text("\n".join(md), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
