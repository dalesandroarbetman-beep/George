#!/usr/bin/env python3
"""Read-only rendered GEO baseline for a public HTTP(S) site."""

from __future__ import annotations

import argparse
import ipaddress
import json
import socket
import sys
import urllib.parse
import urllib.robotparser
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


CONTRACT_VERSION = "geo-scan/1.0"


def validate_public_url(url: str) -> str:
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError("只允许带主机名的公开 HTTP(S) URL")
    if parsed.username or parsed.password:
        raise ValueError("URL 不得包含登录凭据")
    if parsed.hostname.casefold() == "localhost":
        raise ValueError("不允许扫描本地地址")
    try:
        addresses = {item[4][0] for item in socket.getaddrinfo(parsed.hostname, parsed.port or 443)}
    except socket.gaierror as exc:
        raise ValueError(f"域名无法解析：{parsed.hostname}") from exc
    for address in addresses:
        ip = ipaddress.ip_address(address)
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
            raise ValueError("不允许扫描私网、本地或保留地址")
    return urllib.parse.urlunparse(parsed._replace(fragment=""))


class PublicRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        safe_url = validate_public_url(urllib.parse.urljoin(req.full_url, newurl))
        return super().redirect_request(req, fp, code, msg, headers, safe_url)


def fetch_text(url: str, timeout: int) -> dict[str, Any]:
    request = urllib.request.Request(url, headers={"User-Agent": "George-GEO-Scanner/1.0"})
    try:
        opener = urllib.request.build_opener(PublicRedirectHandler())
        with opener.open(request, timeout=timeout) as response:
            final_url = validate_public_url(response.url)
            body = response.read(2_000_000).decode(response.headers.get_content_charset() or "utf-8", errors="replace")
            return {"url": url, "status": response.status, "final_url": final_url, "text": body, "error": None}
    except Exception as exc:
        return {"url": url, "status": None, "final_url": None, "text": "", "error": str(exc)}


def sitemap_urls(text: str) -> list[str]:
    try:
        root = ET.fromstring(text)
    except ET.ParseError:
        return []
    return [node.text.strip() for node in root.findall(".//{*}loc") if node.text and node.text.strip()]


def render_page(url: str, timeout_ms: int) -> dict[str, Any]:
    from playwright.sync_api import sync_playwright

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page()
        def route_public_only(route) -> None:
            request_url = route.request.url
            if urllib.parse.urlparse(request_url).scheme in {"data", "blob", "about"}:
                route.continue_()
                return
            try:
                validate_public_url(request_url)
            except ValueError:
                route.abort("blockedbyclient")
                return
            route.continue_()
        page.route("**/*", route_public_only)
        response = page.goto(url, wait_until="networkidle", timeout=timeout_ms)
        validate_public_url(page.url)
        result = page.evaluate("""() => ({
          title: document.title || '',
          h1: [...document.querySelectorAll('h1')].map(x => x.innerText.trim()).filter(Boolean),
          h2: [...document.querySelectorAll('h2')].map(x => x.innerText.trim()).filter(Boolean),
          canonical: document.querySelector('link[rel="canonical"]')?.href || null,
          robots: document.querySelector('meta[name="robots"]')?.content || null,
          description: document.querySelector('meta[name="description"]')?.content || null,
          text_length: document.body?.innerText?.trim().length || 0,
          jsonld: [...document.querySelectorAll('script[type="application/ld+json"]')].map(x => x.textContent || '')
        })""")
        result["url"] = page.url
        result["status"] = response.status if response else None
        browser.close()
    types: list[str] = []
    for raw in result.pop("jsonld"):
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            continue
        nodes = data if isinstance(data, list) else data.get("@graph", [data]) if isinstance(data, dict) else []
        for node in nodes:
            value = node.get("@type") if isinstance(node, dict) else None
            types.extend(value if isinstance(value, list) else [value] if value else [])
    result["jsonld_types"] = list(dict.fromkeys(types))
    return result


def build_result(site: str, robots: dict[str, Any], sitemap: dict[str, Any], page: dict[str, Any]) -> dict[str, Any]:
    observed_at = datetime.now(timezone.utc).isoformat()
    page_url = str(page.get("url") or site)

    def observation(summary: str, url: str, evidence: str) -> dict[str, str]:
        return {
            "summary": summary,
            "url": url,
            "observed_at": observed_at,
            "evidence_summary": evidence,
        }

    risks = []
    if not page.get("h1"):
        risks.append(observation("首页缺少 H1", page_url, "渲染后的 DOM 中未找到非空 h1 元素。"))
    if not page.get("canonical"):
        risks.append(observation("首页缺少 canonical", page_url, "渲染后的 DOM 中未找到 canonical 链接。"))
    if not page.get("description"):
        risks.append(observation("首页缺少 meta description", page_url, "渲染后的 DOM 中未找到 meta description。"))
    if page.get("text_length", 0) < 300:
        risks.append(observation(
            "渲染正文过短，可能仅获取到应用壳", page_url,
            f"渲染正文字符数为 {page.get('text_length', 0)}，低于最小基线 300。",
        ))
    positives = []
    if robots.get("status") == 200:
        positives.append(observation("robots.txt 可访问", str(robots.get("final_url") or robots.get("url")), "HTTP 状态为 200。"))
    if sitemap.get("status") == 200:
        positives.append(observation("sitemap 可访问", str(sitemap.get("final_url") or sitemap.get("url")), "HTTP 状态为 200。"))
    if page.get("text_length", 0) >= 300:
        positives.append(observation(
            "渲染页面包含可提取正文", page_url,
            f"渲染正文字符数为 {page.get('text_length', 0)}。",
        ))
    return {
        "contract_version": CONTRACT_VERSION,
        "site": site,
        "scanned_at": observed_at,
        "mode": "read_only_rendered_browser",
        "robots": {key: robots.get(key) for key in ("url", "status", "final_url", "error")},
        "sitemap": {
            **{key: sitemap.get(key) for key in ("url", "status", "final_url", "error")},
            "urls": sitemap_urls(str(sitemap.get("text", ""))),
        },
        "pages": [page],
        "observations": {"positive": positives, "risks": risks},
        "limits": ["仅扫描公开页面", "扫描结果不是事实批准", "未检查登录后内容或提交任何表单"],
    }


def write_outputs(result: dict[str, Any], out: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    (out / "scan.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    offsite = {
        "contract_version": CONTRACT_VERSION,
        "site": result["site"],
        "anchors": [],
        "missing": ["本次最小基线未执行站外公开实体锚点检索"],
    }
    (out / "offsite.json").write_text(json.dumps(offsite, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    page = result["pages"][0]
    lines = [
        "# GEO 公开站点基线",
        "",
        f"- 站点：{result['site']}",
        f"- 扫描时间：{result['scanned_at']}",
        f"- 页面状态：{page.get('status', 'unknown')}",
        f"- 标题：{page.get('title') or '未提供'}",
        "",
        "## 可确认观察",
        "",
        *[f"- {item['summary']}（{item['url']}；{item['evidence_summary']}）" for item in result["observations"]["positive"]],
        "",
        "## 风险与待核验项",
        "",
        *([f"- {item['summary']}（{item['url']}；{item['evidence_summary']}）" for item in result["observations"]["risks"]] or ["- 本次最小检查未发现结构缺口"]),
        "",
        "## 限制",
        "",
        *[f"- {item}" for item in result["limits"]],
    ]
    (out / "baseline.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="只读扫描公开站点并生成 GEO 基线")
    parser.add_argument("--url", default="https://www.yohodiy.com/")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--timeout", type=int, default=30)
    args = parser.parse_args()
    try:
        site = validate_public_url(args.url)
        robots_url = urllib.parse.urljoin(site, "/robots.txt")
        sitemap_url = urllib.parse.urljoin(site, "/sitemap.xml")
        robots = fetch_text(robots_url, args.timeout)
        sitemap = fetch_text(sitemap_url, args.timeout)
        policy = urllib.robotparser.RobotFileParser()
        policy.set_url(robots_url)
        policy.parse(str(robots.get("text", "")).splitlines())
        if robots.get("status") == 200 and not policy.can_fetch("George-GEO-Scanner/1.0", site):
            raise ValueError("robots.txt 不允许当前扫描器访问目标页面")
        page = render_page(site, args.timeout * 1000)
        result = build_result(site, robots, sitemap, page)
        write_outputs(result, args.out)
    except Exception as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2
    print(json.dumps({"ok": True, "out": str(args.out), "contract_version": CONTRACT_VERSION}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
