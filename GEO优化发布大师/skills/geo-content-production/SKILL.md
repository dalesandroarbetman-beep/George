---
name: geo-content-production
description: "Produce fact-gated English GEO master drafts and native Reddit, Quora, Indie Hackers, X, LinkedIn, and Facebook variants from an approved architecture brief and fact cards. Score and return drafts for human review; do not publish."
---

# GEO Content Production

## User-visible language rule

External forum copy defaults to English, but every file delivered for user review must be Chinese or English with a complete Chinese translation. This applies to the master draft, platform variants, disclosure, limitations, quality notes, and approval instructions. Do not deliver an English-only draft file.

## Required input

Approved target question, audience, fact-card IDs, source records, prohibited claims, official destination, platform, CTA, reviewer, and due date. If any fact is `pending`, either omit it or label the uncertainty; never upgrade it silently.

## YOHO identity guardrail

Use `YOHO` as the only public English brand name and link only to `https://www.yohodiy.com/`. Do not proactively name a legal entity in forum copy. Preserve legal-entity evidence only in source notes unless the approval record explicitly authorizes disclosure.

## Drafting rules

- Master draft answers the question directly, then gives evidence, context, limitations, and one CTA.
- Each H2/H3 starts with a self-contained answer sentence that can be quoted without losing scope.
- Make each platform version native: Reddit discussion, Quora answer, Indie Hackers build lesson, X short claim/thread, LinkedIn professional lesson, Facebook scenario prompt.
- Keep affiliation transparent; never simulate a customer, independent reviewer, credential, metric, or third-party endorsement.
- Record `angle_difference` and source IDs for every variant. Do not copy the master verbatim.

## Self-check

Check factual traceability, answer completeness, evidence, limitations, natural language, platform constraints, disclosure, sensitive/forbidden claims, and duplicate phrasing. Return `ready` only when the checklist passes; otherwise return `blocked` or `pending` with reasons.

The archived scorer is useful after its input contract is confirmed; do not assume its China-platform references apply to foreign forums.
