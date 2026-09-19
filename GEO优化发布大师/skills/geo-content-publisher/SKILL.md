---
name: geo-content-publisher
description: "Plan and track manual GEO publishing from approved platform drafts. Build calendars, approval queues, per-platform execution packs, URL logs, and measured review notes; never log in or publish without explicit item-level authorization."
---

# GEO Content Publisher

## State machine

内容成熟度和发布状态分开记录。成熟度为 `concept → experimental → release_candidate`；发布状态由追加式事件派生为 `draft → pending_approval → approved → published → verified`，任何状态都可因未解除的阻断事件显示为 `blocked`。

`approved` 需要用户对内容 ID、版本、平台和具体主题的明确确认。`published` 需要用户回传真实 URL 与时间。不要从文件名、截图、计划日期或聊天中的笼统同意推断状态。

## Manual execution pack

For each platform include final text, title/first line, disclosure, destination URL, media slot, community rule checks, prohibited-claim check, suggested timing, and fields for actual URL/result. Do not treat a generated file, screenshot, or planned slot as proof of publication.

用户可见执行包必须是中文，或英文发布文本附完整中文翻译。审核包和发布包都必须包含清单及 SHA-256；审核包必须标记 `publishable=false`。`publish` 模式只接受选定的 `release_candidate`，并要求质量通过、具体问题/社区 URL、规则核验日期、发布负责人、披露位置，以及与版本、平台、目标和正文哈希完全一致的批准事件。

For this project, the destination URL defaults to `https://www.yohodiy.com/`; use `YOHO` as the public brand and omit legal-entity naming unless the approval queue contains an explicit disclosure decision.

## Calendar and review

Schedule only the requested horizon. Keep a per-item owner, dependency, status, master path, platform difference, reviewer, and evidence path. Weekly metrics must state method, date, sample size, and limitations; use `待测`/`unknown` instead of invented values.

单篇发布是操作链路冒烟测试，不是渠道效果结论。渠道评估至少区分：能否发布、是否存活/收录、是否产生合格互动或引荐、不同问题/社区的样本差异。最终发布始终由用户人工操作。
