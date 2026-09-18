---
name: geo-content-publisher
description: "Plan and track manual GEO publishing from approved platform drafts. Build calendars, approval queues, per-platform execution packs, URL logs, and measured review notes; never log in or publish without explicit item-level authorization."
---

# GEO Content Publisher

## State machine

`draft → queued → approved → published → verified`; any state may become `blocked`. `approved` requires explicit user confirmation for the listed content IDs and platforms. `published` requires a real URL and timestamp returned by the user.

## Manual execution pack

For each platform include final text, title/first line, disclosure, destination URL, media slot, community rule checks, prohibited-claim check, suggested timing, and fields for actual URL/result. Do not treat a generated file, screenshot, or planned slot as proof of publication.

For this project, the destination URL defaults to `https://www.yohodiy.com/`; use `YOHO` as the public brand and omit legal-entity naming unless the approval queue contains an explicit disclosure decision.

## Calendar and review

Schedule only the requested horizon. Keep a per-item owner, dependency, status, master path, platform difference, reviewer, and evidence path. Weekly metrics must state method, date, sample size, and limitations; use `待测`/`unknown` instead of invented values.

The archived publisher script has a Python 3.11 f-string syntax error and remains blocked until patched and tested. Manual Markdown/JSON execution packs are the fallback.
