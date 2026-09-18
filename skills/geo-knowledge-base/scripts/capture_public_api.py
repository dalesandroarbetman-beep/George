#!/usr/bin/env python3
"""Capture allowlisted public API responses used by the YOHO DIY storefront."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qs, urlparse


ALLOWLIST = {
    "agent_geo_entries",
    "footer_columns",
    "home_services",
    "home_top_nav_categories",
    "nav_items",
    "site_config",
}
SITE_CONFIG_KEYS = {
    "display_currency",
    "footer_company_name",
    "footer_company_name_translations",
    "footer_copyright",
    "footer_copyright_translations",
    "footer_icp",
    "footer_icp_translations",
    "footer_slogan",
    "footer_slogan_translations",
    "og_description",
    "og_title",
    "seo_author",
    "seo_description",
    "seo_keywords",
    "seo_robots",
    "seo_title",
    "site_domain",
    "site_name",
}
PAGES = (
    "https://www.yohodiy.com/",
    "https://www.yohodiy.com/products",
    "https://www.yohodiy.com/accessory-products",
    "https://www.yohodiy.com/customize",
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def main() -> int:
    parser = argparse.ArgumentParser(description="Capture public YOHO DIY data responses")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--wait-ms", type=int, default=18000)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    from playwright.sync_api import sync_playwright

    manifest = {
        "captured_at": utc_now(),
        "allowlist": sorted(ALLOWLIST),
        "pages": [],
        "responses": [],
        "errors": [],
        "excluded_data": ["accounts", "customization histories", "orders", "payments", "reviews", "user records"],
    }
    captured_urls: set[str] = set()

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page()

        def capture(response) -> None:
            parsed = urlparse(response.url)
            if "/rest/v1/" not in parsed.path:
                return
            table = parsed.path.rsplit("/", 1)[-1]
            if table not in ALLOWLIST or response.url in captured_urls:
                return
            if table == "site_config":
                query = parse_qs(parsed.query)
                raw_key = query.get("key", [""])[0]
                if raw_key.startswith("eq."):
                    raw_key = raw_key[3:]
                if raw_key and raw_key not in SITE_CONFIG_KEYS:
                    return
            captured_urls.add(response.url)
            try:
                payload = response.json()
                digest = hashlib.sha256(response.url.encode("utf-8")).hexdigest()[:12]
                filename = f"{table}-{digest}.json"
                record = {
                    "table": table,
                    "source_url": response.url,
                    "status": response.status,
                    "captured_at": utc_now(),
                    "data": payload,
                }
                (args.out / filename).write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
                manifest["responses"].append({
                    "table": table,
                    "file": filename,
                    "status": response.status,
                    "records": len(payload) if isinstance(payload, list) else 1,
                })
            except Exception as exc:  # pragma: no cover - network dependent
                manifest["errors"].append({"stage": "response", "table": table, "url": response.url, "error": str(exc)})

        page.on("response", capture)
        for url in PAGES:
            page_record = {"url": url, "started_at": utc_now()}
            try:
                response = page.goto(url, wait_until="domcontentloaded", timeout=40_000)
                page.wait_for_timeout(max(0, args.wait_ms))
                page_record.update({"status": response.status if response else None, "final_url": page.url})
            except Exception as exc:  # pragma: no cover - network dependent
                page_record["error"] = str(exc)
                manifest["errors"].append({"stage": "page", "url": url, "error": str(exc)})
            manifest["pages"].append(page_record)
        browser.close()

    manifest["finished_at"] = utc_now()
    (args.out / "api_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0 if manifest["responses"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
