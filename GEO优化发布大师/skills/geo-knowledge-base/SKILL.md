---
name: geo-knowledge-base
description: "Crawl the public rendered pages of yohodiy.com and turn them into canonical, versioned GEO fact cards with provenance, approval status, expiry, and conflict handling. Use before drafting whenever site facts or later knowledge-base exports are needed."
---

# GEO Knowledge Base

本 Skill 是事实闸门，不是文案写手。默认抓取 `https://www.yohodiy.com/` 的公开渲染页面，把首页、关于、服务、帮助、配送/退换、定制、商品和公开分类整理成可追溯事实卡；Markdown、Word、PDF、表格或数据库导出可作为补充来源。

## Site crawl profile

- 首要域名：`www.yohodiy.com`。
- 抓取方式：先读 `robots.txt` 和 sitemap，再用真实浏览器渲染页面；不能只依赖静态 HTML，因为该站点返回的是动态应用壳。
- 允许范围：公开首页、产品/分类、定制、About、Why Choose Us、FAQ、Shipping Info、Return Policy、Warranty、Craftsmanship、尺寸/宝石/包装指南、Brand Story、Contact、Partnership、Media Coverage 等页面。
- 禁止范围：`/admin/`、`/admin`、`/checkout`、`/payment/`、`/orders/`、`/user/`、`/after-sales/`、`/review/`，以及任何需要登录的页面。
- sitemap 当前声明的 `diy.lsdit.com` 作为候选源记录，不自动当作品牌事实源；只有当渲染页面确认同一实体、同一内容和公开可访问时才建立关联。
- 商品价格、库存、优惠、活动和首页推荐属于时效性事实，必须保存抓取时间和复核日期，不得写成长期品牌事实。

## Canonical identity decisions

- Canonical public English brand: `YOHO`.
- Canonical citation/source host: `https://www.yohodiy.com/`.
- Legal entity evidence remains in the fact cards for traceability, but is not proactively exposed in forum copy unless separately approved.
- `YOHE/YOUNG`, `Yoho Origin`, and `YOHO DIY` remain recorded as observed aliases/evidence; they are not interchangeable public copy.

## Crawl output

运行站点抓取后，至少保存：

- `crawl_manifest.json`：种子 URL、抓取时间、robots、sitemap、页面状态、跳转、错误和范围。
- `pages/*.json`：每个页面的最终 URL、标题、语言、正文摘录、结构化数据、链接和抓取时间。
- `fact_cards.json`：从页面证据提取的事实卡；默认状态为 `pending`，除非用户或负责人批准。
- `crawl_report.md`：动态渲染、缺失页面、冲突字段和下一步人工核验。
- `public_api/`：仅限白名单的公开展示接口响应；不保存账户、订单、支付、评价或用户数据。

不要把“页面能看到”直接等同于“事实已批准”；来源可见性和业务批准是两个独立状态。

## Public API capture and fact-card build

当公开页面由同一动态壳渲染、连续分页容易触发网络失败时，可以从浏览器响应中捕获白名单公开展示接口，再运行：

```text
python scripts/capture_public_api.py --out <api-out>
python scripts/build_fact_cards.py --crawl <crawl-out> --api <api-out> --out <knowledge-out>
```

白名单只允许站点配置中的公开品牌/公司/SEO字段、导航分类、页脚栏目、首页服务和公开 GEO 条目。运行配置、后台路径、分析标识、WhatsApp号码、预览密码等不进入知识库。

## Browser fallback

如果 Python Playwright 不可用，使用已配置的浏览器 CLI 做只读采集：打开页面、等待 `networkidle`、获取 `body` 的渲染文本和 HTML，再把命令输出作为原始证据保存。每次导航后重新获取页面状态，不复用旧引用；不要使用登录态、表单提交或交易页面。

## Fact card

```yaml
fact_id: "FC-..."
subject: "company|product|service|person|case|policy"
claim: "短而明确的事实"
status: "verified|pending|disallowed|expired|conflict"
source_type: "official_page|approved_file|public_source|user_statement"
source_ref: "URL or file path"
evidence_quote: "原文片段"
captured_at: "YYYY-MM-DD"
review_due: "YYYY-MM-DD or null"
approved_channels: ["reddit", "quora"]
notes: "边界、限制和冲突"
```

## 工作方式

1. 先列出来源与文件范围，再提取事实；不把推断写成事实。
2. 同一实体的名称、数字、价格、能力、案例和联系方式分别建卡。
3. `pending` 不可作为硬断言；`disallowed` 和 `conflict` 必须阻断下游。
4. 记录版本、审阅人和复核日期；旧事实不能静默覆盖。
5. 回传给架构师的是批准的 fact card ID；回传给内容生产的是允许使用的 claim 和来源。

## 知识库未就绪

可先输出 `knowledge_import_manifest.json` 和“已核实/待核实/禁止使用”三栏清单。不得因为知识库尚在建立就捏造默认产品事实。
