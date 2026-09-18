# YOHO GEO team handoff v0

## Input package

- Fact cards: `output/site-knowledge/yohodiy-knowledge-base-20260918/fact_cards.json`
- Fact review: `output/site-knowledge/yohodiy-knowledge-base-20260918/fact_card_review.md`
- Architecture: `architecture_brief.md`
- Question matrix: `question_matrix.md`

## Team sequence

`geo-scanner → geo-knowledge-base → geo-architect → geo-content-production → geo-quality-gate → geo-content-publisher`

## Handoff contracts

- Scanner returns dated public evidence and reproducible URLs only.
- Knowledge base returns fact-card IDs, status, source, quote, review date, and conflicts.
- Architect returns one chosen question, audience, channel order, CTA, prohibited claims, and owner.
- Content production returns one English master plus native platform variants, with source IDs and angle differences.
- Quality gate returns defects by severity and a disposition; unresolved high-risk defects block approval.
- Publisher returns a manual execution pack and URL log. A planned post or screenshot is not publication evidence.

## Current blocker

Identity and source-host decisions are resolved. Content production is intentionally waiting on the first topic/question, audience, and claim approvals. This prevents the team from turning public-site observations into unsupported forum promises.
