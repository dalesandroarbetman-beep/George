---
name: geo-content-publisher
description: "Plan and track manual GEO publishing from approved platform drafts. Build calendars, approval queues, per-platform execution packs, URL logs, and measured review notes; never log in or publish without explicit item-level authorization."
---

# GEO Content Publisher

## State machine

`draft → queued → approved → published → verified`; any state may become `blocked`. `approved` requires explicit user confirmation for the listed content IDs and platforms. `published` requires a real URL and timestamp returned by the user.

## Manual execution pack

For each platform include final text, title/first line, disclosure, destination URL, media slot, community rule checks, prohibited-claim check, suggested timing, and fields for actual URL/result. Do not treat a generated file, screenshot, or planned slot as proof of publication.

Every user-visible execution pack must be in Chinese or include the complete Chinese translation alongside the English publication text. The English text may remain the copy-paste version for the external platform; the Chinese translation is required for user review.

For this project, the destination URL defaults to `https://www.yohodiy.com/`; use `YOHO` as the public brand and omit legal-entity naming unless the approval queue contains an explicit disclosure decision.

## Calendar and review

Schedule only the requested horizon. Keep a per-item owner, dependency, status, master path, platform difference, reviewer, and evidence path. Weekly metrics must state method, date, sample size, and limitations; use `待测`/`unknown` instead of invented values.

Use `scripts/build_execution_pack.py` to validate approved draft metadata and build a versioned JSON pack plus a Chinese approval queue. The helper is always local and dry-run: it never logs in, posts, or changes a platform. The archived script is deprecated and no longer an execution path.
