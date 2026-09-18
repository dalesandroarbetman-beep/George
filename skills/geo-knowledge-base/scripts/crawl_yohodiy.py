#!/usr/bin/env python3
"""Read-only rendered crawl for the public YOHO DIY storefront.

The site is a JavaScript application, so static HTML alone is not enough for
the knowledge-base import. This helper records rendered page evidence and
never logs in, submits forms, or visits account/transaction paths.
"""

from __future__ import annotations

import argparse
import json
import re
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_URL = "https://www.yohodiy.com/"
BLOCKED_PREFIXES = (
    "/admin",
    "/checkout",
    "/payment/",
    "/orders/",
    "/user/",
    "/after-sales/",
    "/review/",
)
SEED_PATHS = (
    "/",
    "/products",
    "/accessory-products",
    "/customize",
    "/customize/letter",
    "/customize/accessory",
    "/customize/splice",
    "/design-square",
    "/help",
    "/about-us",
    "/why-choose-us",
    "/faq",
    "/shipping-info",
    "/return-policy",
    "/warranty",
    "/craftsmanship",
    "/ring-size-guide",
    "/necklace-length-guide",
    "/packaging",
    "/gemstone-guide",
    "/diamond-4c",
    "/brand-story",
    "/order-help",
    "/contact-us",
    "/partnership",
    "/media-coverage",
)


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def fetch_text(url: str, timeout: int = 20) -> tuple[int, str, str | None]:
    request = urllib.request.Request(url, headers={"User-Agent": "GEO-Knowledge-Base/0.1"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        body = response.read().decode("utf-8", errors="replace")
        return response.status, body, response.geturl()


def parse_sitemap(text: str) -> list[str]:
    try:
        root = ET.fromstring(text)
    except ET.ParseError:
        return re.findall(r"<loc>\s*(.*?)\s*</loc>", text, flags=re.I | re.S)
    return [element.text.strip() for element in root.iter() if element.tag.endswith("loc") and element.text]


def is_allowed(url: str, host: str) -> bool:
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme not in {"http", "https"} or parsed.netloc.lower() != host.lower():
        return False
    path = parsed.path or "/"
    return not any(path.startswith(prefix) for prefix in BLOCKED_PREFIXES)


def normalize_link(base: str, href: str) -> str | None:
    if not href or href.startswith(("mailto:", "tel:", "javascript:", "#")):
        return None
    return urllib.parse.urljoin(base, href).split("#", 1)[0]


def main() -> int:
    parser = argparse.ArgumentParser(description="Crawl public rendered YOHO DIY pages")
    parser.add_argument("--url", default=DEFAULT_URL)
    parser.add_argument("--out", type=Path, default=Path("site-knowledge/yohodiy-crawl"))
    parser.add_argument("--max-pages", type=int, default=40)
    parser.add_argument("--delay", type=float, default=0.5)
    parser.add_argument("--page-timeout", type=int, default=25)
    parser.add_argument("--settle-ms", type=int, default=10000)
    parser.add_argument("--seed-file", type=Path)
    parser.add_argument("--no-discovery", action="store_true")
    args = parser.parse_args()

    origin = urllib.parse.urlparse(args.url)
    host = origin.netloc
    args.out.mkdir(parents=True, exist_ok=True)
    pages_dir = args.out / "pages"
    pages_dir.mkdir(exist_ok=True)
    started = now()
    manifest = {
        "seed_url": args.url,
        "started_at": started,
        "crawler": "rendered-playwright-read-only",
        "robots": None,
        "sitemap": None,
        "candidate_sitemap_urls": [],
        "pages": [],
        "errors": [],
        "blocked_prefixes": list(BLOCKED_PREFIXES),
    }

    robots_url = urllib.parse.urljoin(args.url, "/robots.txt")
    sitemap_url = urllib.parse.urljoin(args.url, "/sitemap.xml")
    try:
        status, text, final = fetch_text(robots_url)
        manifest["robots"] = {"url": robots_url, "status": status, "final_url": final, "text": text}
        found = re.findall(r"(?im)^\s*Sitemap:\s*(\S+)\s*$", text)
        manifest["candidate_sitemap_urls"] = found
    except Exception as exc:  # pragma: no cover - network dependent
        manifest["errors"].append({"stage": "robots", "url": robots_url, "error": str(exc)})
    try:
        status, text, final = fetch_text(sitemap_url)
        manifest["sitemap"] = {"url": sitemap_url, "status": status, "final_url": final, "urls": parse_sitemap(text)}
    except Exception as exc:  # pragma: no cover - network dependent
        manifest["errors"].append({"stage": "sitemap", "url": sitemap_url, "error": str(exc)})

    if args.seed_file:
        queue = [line.strip() for line in args.seed_file.read_text(encoding="utf-8").splitlines() if line.strip()]
        manifest["seed_file"] = str(args.seed_file)
    else:
        queue = [urllib.parse.urljoin(args.url, path) for path in SEED_PATHS]
        for url in manifest.get("sitemap", {}).get("urls", []):
            if is_allowed(url, host):
                queue.append(url)
    seen: set[str] = set()

    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:  # pragma: no cover - environment dependent
        manifest["errors"].append({"stage": "playwright_import", "error": str(exc), "next": "Install Python Playwright or use the approved browser CLI fallback."})
        manifest["finished_at"] = now()
        manifest["page_count"] = 0
        (args.out / "crawl_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        report = [
            "# YOHO DIY crawl report",
            "",
            f"- Seed: `{args.url}`",
            f"- Captured: `{manifest['finished_at']}`",
            "- Status: `blocked` — rendered browser dependency is unavailable in the Python runtime.",
            "- Robots and sitemap were read successfully; no page facts were promoted.",
            "",
            "## Next action",
            "",
            "- Install Python Playwright in the approved environment, or run the browser CLI fallback and import its rendered snapshot.",
            "- Keep all extracted facts at `pending` until source and business approval are recorded.",
        ]
        (args.out / "crawl_report.md").write_text("\n".join(report) + "\n", encoding="utf-8")
        return 2

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page()
        while queue and len(seen) < args.max_pages:
            url = queue.pop(0)
            if url in seen or not is_allowed(url, host):
                continue
            seen.add(url)
            record = {"requested_url": url, "captured_at": now()}
            try:
                response = page.goto(url, wait_until="domcontentloaded", timeout=args.page_timeout * 1000)
                deadline = time.monotonic() + max(0, args.settle_ms) / 1000
                while time.monotonic() < deadline:
                    if len(page.locator("body").inner_text(timeout=3000).strip()) >= 100:
                        break
                    page.wait_for_timeout(500)
                record["status"] = response.status if response else None
                record["final_url"] = page.url
                payload = page.evaluate(
                    """() => ({
                      title: document.title,
                      lang: document.documentElement.lang || null,
                      text: (document.body?.innerText || '').slice(0, 120000),
                      canonical: document.querySelector('link[rel=canonical]')?.href || null,
                      meta: Array.from(document.querySelectorAll('meta[name],meta[property]')).map(x => ({name:x.name||x.property, content:x.content||''})),
                      jsonld: Array.from(document.querySelectorAll('script[type="application/ld+json"]')).map(x => x.textContent || ''),
                      links: Array.from(document.querySelectorAll('a[href]')).map(x => x.href)
                    })"""
                )
                record.update({key: payload.get(key) for key in ("title", "lang", "text", "canonical", "meta", "jsonld")})
                if len((record.get("text") or "").strip()) < 100:
                    record["warning"] = "Rendered body text remained short after settle timeout; treat page as shell/partial evidence."
                links = sorted({normalize_link(page.url, href) for href in payload.get("links", [])})
                links = [link for link in links if link and is_allowed(link, host)]
                record["links"] = links[:500]
                filename = f"{len(seen):04d}.json"
                (pages_dir / filename).write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
                manifest["pages"].append({"file": f"pages/{filename}", "requested_url": url, "final_url": page.url, "status": record["status"], "title": record.get("title")})
                (args.out / "crawl_manifest.partial.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
                if not args.no_discovery:
                    for link in links:
                        if link not in seen and link not in queue:
                            queue.append(link)
            except Exception as exc:  # pragma: no cover - network dependent
                record["error"] = str(exc)
                manifest["errors"].append({"stage": "page", **record})
                (args.out / "crawl_manifest.partial.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
            time.sleep(max(0.0, args.delay))
        browser.close()

    manifest["finished_at"] = now()
    manifest["page_count"] = len(manifest["pages"])
    (args.out / "crawl_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    retry_urls = sorted({item.get("requested_url") for item in manifest["errors"] if item.get("requested_url")})
    (args.out / "retry_urls.txt").write_text("\n".join(retry_urls) + ("\n" if retry_urls else ""), encoding="utf-8")
    report = [
        "# YOHO DIY crawl report",
        "",
        f"- Seed: `{args.url}`",
        f"- Captured: `{manifest['finished_at']}`",
        f"- Rendered pages: `{manifest['page_count']}`",
        "- Status: source evidence only; fact cards remain `pending` until reviewed.",
        "",
        "## Notes",
        "",
        "- Static HTML is not treated as complete because the storefront is JavaScript-rendered.",
        "- Account, transaction, review, and admin paths are excluded.",
        "- Prices, stock, promotions, and recommendations require a review date.",
    ]
    (args.out / "crawl_report.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    return 0 if not manifest["errors"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
