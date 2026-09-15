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
4. If the item passes the risk gate, extract only supported keywords. Product data has priority for material and process. Apply the user-approved title mappings in [material rules](references/material-rules.md): source `304不锈钢` is displayed as `钛钢`, and any explicit source `14K` or `18K` field is displayed as the matching `真空电镀14K金` or `真空电镀18K金`. A clearly visible zircon decoration may be added as `锆石` when product data omits it, following the same reference. Do not invent `镶嵌`, `天然`, `人工`, `合成`, or purity claims.
5. Generate three Chinese title options by default. The first is the preferred natural title; the second and third may test a different valid order or lower-priority candidate word. Use Chinese commas and no full stop.

## Title construction

Prefer this order when the fields exist:

`系列/风格 + 造型/可见图案细节 + 主体材质 + 工艺 + 款式/分类`

Use one or two image- or data-supported style words by default before the shape. Favor useful style descriptors such as `复古`, `简约`, `甜美`, `个性`, or `徽章风` when they fit the item; do not add contradictory, weak, or unsupported style words merely to lengthen the title. Use the most specific visible shape wording supported by the image: retain a visible motif detail such as `字母` after the primary shape when it helps distinguish the item. When material and process are both supported, keep them together as a continuous phrase, such as `钛钢真空电镀14K金`. When the source category is `配件` and the image clearly shows a pendant, `吊坠配件` is an allowed ending.

Omit missing or weak fields. Do not put SKU, internal codes, brand names, authorization, collaboration, patent, exclusivity, or unsupported marketing claims in the title. `宗教` and `宗教风` are forbidden title words, even when the design contains a cross or other related motif. Color, scene, gift, size, weight, quantity, and packaging are omitted by default unless they define the wearing form or the user explicitly requests them. Do not use `爆款`, `顶级`, `奢华`, or `正品`.

Use the exact approved keyword form, including the user-approved title mappings: `304不锈钢` → `钛钢`; explicit `14K` → `真空电镀14K金`; explicit `18K` → `真空电镀18K金`. Do not apply any other silent normalization. New or uncertain words go into the response as `新关键词/待确认`, not into the confirmed vocabulary.

## Shared improvement protocol

The copy in George is the canonical version of this Skill. Normal title generation is read-only: members and agents must not edit `SKILL.md`, references, or the confirmed vocabulary during ordinary use. Members do not need to submit files, create branches, or push to GitHub.

- Do not require the member to label or record improvements manually. Infer improvement signals from the current conversation, including explicit corrections, accepted/rejected title options, repeated preferences, new words, material corrections, and disputed risk decisions.
- At the end of the day, when the member asks `汇总今日优化日志` or `汇总我的使用习惯`, summarize only improvement points from the current conversation. Do not claim to have read other members' private conversations or tasks.
- The daily log is sent by the member to the maintainer. The maintainer decides what to merge into the canonical Skill or vocabulary.
- A keyword becomes confirmed only after the maintainer or user explicitly approves it. A wording/order rule needs two independent cases or explicit approval. A risk/IP rule always needs human review.

Use [collaboration guidance](references/collaboration.md) for the short daily-log format and the maintainer review rules. Use [style-vocabulary.md](references/style-vocabulary.md) for style candidates and [risk-keywords.md](references/risk-keywords.md) for evidence flags; neither list authorizes unsupported claims.

## Image-only evidence handling

Separate every extracted field into `已确认` (explicit in data, user-confirmed, or clearly legible/visible) and `待确认` (ambiguous from the image). Use confirmed fields in titles. Keep uncertain fields out of the title and list them under `notes` or `new_keywords`. An image may support visible form and a clearly recognizable decorative stone, but it cannot by itself prove alloy grade, plating, purity, waterproofing, hypoallergenic performance, or a brand/IP relationship.

## Output contract

For a passing item, output the provided SKU (or `未提供SKU`), status, and three titles unless a conflict needs explanation. Use one of the statuses in [data contract](references/data-contract.md). Keep material, shape, and length conflicts visible in the status. When the user requests English output, translate the selected Chinese title and keep it within 80 English characters, counting spaces and punctuation. If over the limit, remove lower-priority style, decoration, and marketing words first while retaining the core shape, category, supported material, and finish; do not add new keywords.

## Confirmed reusable keyword rules

The 2026-09-14 maintainer log confirmed these reusable terms when evidence supports them: `滴釉`, `叠戴`, `不规则`, `蛇骨链`, `女王头像`, `万能扣`, `软陶`, `铜配件`, and `镶嵌锆石`. See [keyword-vocabulary.md](references/keyword-vocabulary.md). A term must not be used merely because it appears in the list.

Read the focused references only when needed:

- [risk-rules.md](references/risk-rules.md) for the risk gate and stop conditions.
- [material-rules.md](references/material-rules.md) for image-supported zircon supplementation and material wording.
- [data-contract.md](references/data-contract.md) for the auto-listing input/output shape.
