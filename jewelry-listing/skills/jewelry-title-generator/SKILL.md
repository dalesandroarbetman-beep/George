---
name: jewelry-title-generator
description: Generate Chinese jewelry product titles from SKU data and images, with a counterfeit or protected-design risk gate and controlled keyword usage. Use for independent-site jewelry listing workflows; do not use for unrelated copywriting or invented product claims.
---

# Jewelry Title Generator

Use this skill only for jewelry title generation. A product image alone is a valid starting input; a SKU and product record can be added when available. The default output is Chinese because the storefront provides language conversion for overseas customers. This skill does not create an upload package or operate an ERP/backend.

## Input modes

- **Image-first:** The user sends one or more images. Identify the visible jewelry category, shape, style, decoration, and any legible material/finish evidence. Do not wait for an SKU unless it is needed to distinguish separate products.
- **SKU-first:** The user sends an SKU or product record, with images optionally attached. Use the record to confirm fields and use images for appearance and risk review.
- **Mixed:** Reconcile the record and image. When they conflict, preserve the conflict in `status` and `notes`; do not silently choose an unsupported value.

If several images show the same item, treat them as one product. If one image contains several distinct items and the user has not identified the target, ask which item to title before generating.

## Required sequence

1. Identify the SKU and collect the available product record and images. Treat each SKU independently; do not reuse a risk conclusion from another SKU.
2. Run the risk gate before writing any title. Focus on suspected imitation of a recognizable brand and suspected copying of a protected distinctive design or design patent. Common crosses, skulls, hearts, letters, chains, and ordinary logos are not automatically risky.
3. If risk cannot be resolved because reverse search or visual evidence fails, mark `风险无法确认`, do not generate a title, and ask for review. If imitation or protected-design risk is found, mark `PASS/禁止上架` and do not generate a title.
4. If the item passes the risk gate, extract only supported keywords. Product data has priority for material and process. A clearly visible zircon decoration may be added as `锆石` when product data omits it, following [material rules](references/material-rules.md). Do not invent `镶嵌`, `天然`, `人工`, `合成`, plating, or purity claims.
5. Generate three Chinese title options by default. The first is the preferred natural title; the second and third may test a different valid order or lower-priority candidate word. Use Chinese commas and no full stop.

## Title construction

Prefer this order when the fields exist:

`系列/风格 + 造型 + 装饰材质 + 款式 + 成色/主体材质`

Omit missing or weak fields. Do not put SKU, internal codes, brand names, authorization, collaboration, patent, exclusivity, or unsupported marketing claims in the title. Color, scene, gift, size, weight, quantity, and packaging are omitted by default unless they define the wearing form or the user explicitly requests them. Do not use `爆款`, `顶级`, `奢华`, or `正品`.

Use the exact approved keyword form. Do not silently normalize a source term into a synonym. New or uncertain words go into the response as `新关键词/待确认`, not into the confirmed vocabulary.

## Shared improvement protocol

The copy in George is the canonical version of this Skill. Normal title generation is read-only: members and agents must not edit `SKILL.md`, references, or the confirmed vocabulary during ordinary use. Members do not need to submit files, create branches, or push to GitHub.

- Keep any correction, rejected word, useful new word, or disputed risk decision as a short note in the current conversation.
- At the end of the day, when the member asks `汇总今日优化日志`, summarize only improvement points from the current conversation. Do not claim to have read other members' private conversations or tasks.
- The daily log is sent by the member to the maintainer. The maintainer decides what to merge into the canonical Skill or vocabulary.
- A keyword becomes confirmed only after the maintainer or user explicitly approves it. A wording/order rule needs two independent cases or explicit approval. A risk/IP rule always needs human review.

Use [collaboration guidance](references/collaboration.md) for the short daily-log format and the maintainer review rules.

## Image-only evidence handling

Separate every extracted field into `已确认` (explicit in data, user-confirmed, or clearly legible/visible) and `待确认` (ambiguous from the image). Use confirmed fields in titles. Keep uncertain fields out of the title and list them under `notes` or `new_keywords`. An image may support visible form and a clearly recognizable decorative stone, but it cannot by itself prove alloy grade, plating, purity, waterproofing, hypoallergenic performance, or a brand/IP relationship.

## Output contract

For a passing item, output the provided SKU (or `未提供SKU`), status, and three titles unless a conflict needs explanation. Use one of the statuses in [data contract](references/data-contract.md). Keep material, shape, and length conflicts visible in the status. When the user requests English output, translate the selected Chinese title and keep it within 80 English characters by dropping lower-priority words first; do not add new keywords.

Read the focused references only when needed:

- [risk-rules.md](references/risk-rules.md) for the risk gate and stop conditions.
- [material-rules.md](references/material-rules.md) for image-supported zircon supplementation and material wording.
- [data-contract.md](references/data-contract.md) for the auto-listing input/output shape.
