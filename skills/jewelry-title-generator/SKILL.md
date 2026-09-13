---
name: jewelry-title-generator
description: Generate Chinese jewelry product titles from SKU data and images, with a counterfeit or protected-design risk gate and controlled keyword usage. Use for independent-site jewelry listing workflows; do not use for unrelated copywriting or invented product claims.
---

# Jewelry Title Generator

Use this skill when a jewelry SKU, product record, or product image needs a listing title. The default output is Chinese because the storefront provides language conversion for overseas customers.

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

## Output contract

For a passing SKU, output only the SKU, status, and three titles unless a conflict needs explanation. Use one of the statuses in [data contract](references/data-contract.md). Keep material, shape, and length conflicts visible in the status. When the user requests English output, translate the selected Chinese title and keep it within 80 English characters by dropping lower-priority words first; do not add new keywords.

Read the focused references only when needed:

- [risk-rules.md](references/risk-rules.md) for the risk gate and stop conditions.
- [material-rules.md](references/material-rules.md) for image-supported zircon supplementation and material wording.
- [data-contract.md](references/data-contract.md) for the auto-listing input/output shape.
