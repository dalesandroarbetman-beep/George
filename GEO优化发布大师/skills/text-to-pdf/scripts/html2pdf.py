#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
html2pdf — 文字→美观 PDF 的转换核心

用法:
    python3 html2pdf.py <input.html> <output.pdf>
        [--engine auto|playwright|weasyprint]
        [--margin "20mm 17mm 18mm 17mm"]   # 上 右 下 左(或单值); 满版用 "0 0 0 0"
        [--no-footer]                       # 不显示页脚页码(满版/暗色模板用)

引擎策略: 优先 Playwright(Chromium, 美观上限最高), 不可用时自动降级 WeasyPrint。
KCode: 入参校验 / 引擎缺失给修复提示 / 转换后产物自检 / 全程日志。
"""
import os
import sys
import argparse

FOOTER_TEMPLATE = (
    '<div style="font-size:8px;color:#5c6573;width:100%;text-align:center;'
    'font-family:sans-serif;">'
    '<span class="pageNumber"></span> / <span class="totalPages"></span></div>'
)
HEADER_TEMPLATE = '<div></div>'


def log(msg):
    print(f"[html2pdf] {msg}", flush=True)


def _margin_dict(margin):
    p = margin.split()
    n = len(p)
    if n == 1:   t = r = b = l = p[0]              # 四边
    elif n == 2: t = b = p[0]; r = l = p[1]        # 上下, 左右
    elif n == 3: t, b = p[0], p[2]; r = l = p[1]   # 上, 左右, 下
    elif n == 4: t, r, b, l = p                    # 上 右 下 左
    else:
        raise ValueError('margin 支持 1-4 个值(同 CSS 简写), 如 "20mm" 或 "20mm 17mm 18mm 17mm"')
    return {"top": t, "right": r, "bottom": b, "left": l}


def via_playwright(html_path, pdf_path, margin="20mm 17mm 18mm 17mm", footer=True):
    """Chromium 渲染 — 美观上限最高。边距由 --margin 控制。"""
    from playwright.sync_api import sync_playwright
    m = _margin_dict(margin)
    url = "file://" + os.path.abspath(html_path)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        try:
            page = browser.new_page()
            page.goto(url, wait_until="networkidle")
            # 关键: 等所有 @font-face 字体真正加载完成, 否则偶发字形缺失(白页/缺字)
            page.evaluate("() => document.fonts.ready")
            opts = dict(path=pdf_path, format="A4", print_background=True, margin=m)
            if footer:
                opts.update(display_header_footer=True,
                            header_template=HEADER_TEMPLATE,
                            footer_template=FOOTER_TEMPLATE)
            page.pdf(**opts)
        finally:
            browser.close()
    return "playwright"


def via_weasyprint(html_path, pdf_path):
    """纯 Python 兜底 — 无浏览器依赖(边距走 CSS @page)。"""
    from weasyprint import HTML
    HTML(filename=os.path.abspath(html_path)).write_pdf(pdf_path)
    return "weasyprint"


def convert(html_path, pdf_path, engine="auto",
            margin="20mm 17mm 18mm 17mm", footer=True):
    if not os.path.isfile(html_path):
        log(f"错误: 输入 HTML 不存在 -> {html_path}")
        return False
    os.makedirs(os.path.dirname(os.path.abspath(pdf_path)) or ".", exist_ok=True)

    order = {"playwright": ["playwright"], "weasyprint": ["weasyprint"],
             "auto": ["playwright", "weasyprint"]}.get(engine)
    if order is None:
        log(f"错误: 未知引擎 '{engine}'")
        return False

    last_err = None
    for eng in order:
        try:
            log(f"尝试引擎: {eng}")
            if eng == "playwright":
                used = via_playwright(html_path, pdf_path, margin=margin, footer=footer)
            else:
                used = via_weasyprint(html_path, pdf_path)
            if not os.path.isfile(pdf_path) or os.path.getsize(pdf_path) == 0:
                raise RuntimeError("产物缺失或为空")
            log(f"成功: {used} -> {pdf_path} ({os.path.getsize(pdf_path)/1024:.1f} KB)")
            if used == "weasyprint" and engine == "auto":
                log("提示: 已降级到 WeasyPrint, 复杂 CSS 效果可能与 Chromium 略有差异")
            return True
        except ImportError as e:
            last_err = e
            log(f"引擎 {eng} 未安装: {e}")
            log("  修复: pip install playwright && playwright install chromium"
                if eng == "playwright"
                else "  修复: pip install weasyprint (需系统库 pango/cairo)")
        except Exception as e:
            last_err = e
            log(f"引擎 {eng} 失败: {e}")
    log(f"全部引擎失败, 最后错误: {last_err}")
    return False


def main():
    ap = argparse.ArgumentParser(description="HTML -> 美观 PDF")
    ap.add_argument("input_html")
    ap.add_argument("output_pdf")
    ap.add_argument("--engine", default="auto",
                    choices=["auto", "playwright", "weasyprint"])
    ap.add_argument("--margin", default="20mm 17mm 18mm 17mm",
                    help='页边距 "上 右 下 左"(或单值); 满版用 "0 0 0 0"')
    ap.add_argument("--no-footer", action="store_true",
                    help="不显示页脚页码(满版/暗色模板用)")
    args = ap.parse_args()
    ok = convert(args.input_html, args.output_pdf, args.engine,
                 margin=args.margin, footer=not args.no_footer)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
