---
name: geo-scanner
description: "Read-only GEO baseline and public evidence scanner for an official site and its public entity references. Use when the task needs crawlability, extractability, source provenance, offsite anchors, or a reproducible baseline before content planning."
---

# GEO Scanner

扫描只读网站与公开页面，为内容团队提供可复核证据，不替代知识库批准，也不把搜索结果或一次 AI 回答写成长期规律。首版默认检查 `https://www.yohodiy.com/`。

## 输入

- 官方 URL、允许检查的页面范围、目标问题集和目标平台。
- 需要验证的实体字段：公司、品牌、产品、服务、作者、联系方式、案例和公开资料。

## 输出

- `scan.json`：日期、URL、状态码、标题/H1、可抓取文本、结构化数据、robots/sitemap 和缺口。
- `offsite.json`：公开锚点、来源 URL、证据摘要、缺失项和 NAP 冲突。
- `baseline.md`：事实与观察分开，列出下一步动作和限制。

## 硬规则

- 只使用公开、可访问、可引用的页面；不绕过登录、地区限制或反爬。
- 每条结论绑定 URL、抓取日期和原文摘要；无法复核则标为 `uncertain`。
- 不修改网站，不提交表单，不登录，不声称完成发布或收录。
- 将 `discoverable / understandable / trustworthy / citable / in_answer` 分开诊断。

对动态站点先读取 `robots.txt` 和 sitemap，再使用渲染浏览器提取页面正文、链接和结构化数据；静态 HTML 只作为响应证据，不能假定它包含完整页面内容。

使用 `scripts/scan_public_site.py` 生成版本化的 `scan.json`、`offsite.json` 和中文 `baseline.md`。脚本仅访问公开 HTTP(S) 页面，拒绝本地/私网地址，先读取 robots 与 sitemap，再用 Playwright 渲染主页；不会登录、提交表单或修改网站。原压缩包脚本已弃用，不再作为执行入口。
