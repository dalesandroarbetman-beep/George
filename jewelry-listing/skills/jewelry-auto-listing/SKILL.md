---
name: jewelry-auto-listing
description: "Prepare and review single-SKU Chinese jewelry listings for an independent store: resolve product data, check source and size images, apply title/IP risk gates, create missing creative assets when authorized, and produce a reviewable listing package. Use for jewelry listing operations, not general copywriting or bulk multi-SKU publishing."
---

# Jewelry Auto Listing

Use this skill for the first-version independent-site jewelry workflow. The default unit is one single-SKU product. Multi-SKU and combination products are not auto-submitted; identify them and stop for human review.

## Required sequence

1. Collect the product Excel/JSON path, the SKU, the writable review root, and the current local/NAS product-library path. Paths must be supplied or selected on each computer; never assume the current machine's path.
2. Resolve exactly one SKU from the product data. Use the ordinary-product data area as the authoritative source when ERP data is available. Keep the source library read-only.
3. Locate the white-background main image and the size image. A size image is a hard gate: if it is missing, or its SKU, length, or weight is missing/unreadable, stop before opening the backend.
4. Run the title/IP/material risk gate before generating a final title. Read [references/title-and-risk.md](references/title-and-risk.md).
5. Reuse available model and scene images. If either is missing and the user has authorized image generation, use the CreatOK image-generation skill with the category prompt rules in [references/image-rules.md](references/image-rules.md). Keep the product appearance faithful to the main image.
6. Create a batch/SKU review package under the writable review root. Read [references/package-contract.md](references/package-contract.md).
7. Only after the package is complete and the user explicitly authorizes backend work, open the already-authorized logged-in backend, fill the form in one batch, validate once, submit once, and immediately unpublish the created item for human review. Do not invent a draft button or use a replacement browser session.
8. Verify the post-submit state once. If browser controls or the logged-in session fail, stop and report the concrete blocker; do not retry indefinitely or submit again.

## Fixed first-version fields

- Title language: Chinese. Overseas display is handled by the storefront language switch.
- Brand: `Carlidana`.
- Category: use the confirmed jewelry style/category vocabulary; new terms are reported as `new_keywords` for review.
- Price: fill the independent-store sale price with the ERP basic sale price. Leave original price blank.
- Shipping template: leave blank in version 1 and remind the reviewer to fill it after the template is imported.
- Upload exactly six images, in this order: one model image, three scene images, one main image, one size image.
- Product detail and gallery use the same six-image order. For version-1 multi-SKU work, do not automate; the later rule may use only the first five size images when explicitly enabled.

## Hard stops and safety

- Missing size image or incomplete size facts => write the warning, create the review record if possible, and do not open or submit the backend form.
- Missing model/scene images alone is not a hard stop when authorized generation is available; otherwise mark them missing and wait.
- A possible imitation, protected distinctive design, or unresolved risk => do not generate a final title or submit; preserve the risk status and request human review.
- Do not claim natural stone, plating, purity, solid gold, authorization, exclusivity, or patent safety without evidence. If data says `18K` but material is absent, keep it as an input keyword only and mark material confirmation when needed.
- Never modify, rename, move, or delete files in the source product library. Only copy source images into the writable review package; generated images may be added there.
- Do not put API keys, cookies, browser caches, or private configuration in the skill or review package.

## Output

Always preserve the machine-readable package and the human-readable checklist. The package must include `status`, `risk_summary`, `new_keywords`, `notes`, title candidates, selected fields, image order, warnings, and the next action. See [references/package-contract.md](references/package-contract.md).

## Optional deterministic helper

Use `scripts/auto_listing.py` to read JSON/Excel and create the package without an LLM. It accepts `--source-root`, `--source-product-dir`, and `--review-root`; pass the paths for the current computer. It does not submit the backend form.
