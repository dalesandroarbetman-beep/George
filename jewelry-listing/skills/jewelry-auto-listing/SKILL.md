---
name: jewelry-auto-listing
description: "Prepare and review single-SKU Chinese jewelry listings for an independent store: resolve product data, check source and size images, apply title/IP risk gates, mark missing creative assets for manual补图, and produce a reviewable listing package. Use for jewelry listing operations, not general copywriting or bulk multi-SKU publishing."
---

# Jewelry Auto Listing

Use this skill for the first-version independent-site jewelry workflow. The default unit is one single-SKU product. Multi-SKU and combination products are not auto-submitted; identify them and stop for human review.

## Required sequence

1. Collect the product Excel/JSON path, the SKU, and either a portable config file or the writable review root plus current local/NAS product-library path. Paths must be supplied or selected on each computer; never assume the current machine's path. A config file may contain `source_root`, `review_root`, `source_product_dir`, and `asset_dir`; command-line values override it.
2. Resolve exactly one SKU from the product data. Use the ordinary-product data area as the authoritative source when ERP data is available. Keep the source library read-only.
3. Locate the white-background main image and the size image. Prefer a prebuilt image index; when an index is provided, use it only and do not fall back to a network scan. Main image and size image are hard gates: if either is missing, or the size image's SKU, length, or weight is missing/unreadable, stop before opening the backend.
4. Run the title/IP/material risk gate before generating a final title. Read [references/title-and-risk.md](references/title-and-risk.md).
5. Reuse available model and scene images. In the fixed rules-only program, missing model/scene images are only marked pending and never trigger image generation or an external-service dependency. An optional external image module may be run separately after explicit authorization; its outputs can then be placed in the review package and reprocessed.
6. Create a batch/SKU review package under the writable review root. Read [references/package-contract.md](references/package-contract.md).
7. The preparation program only produces the complete versioned package; it never fills a backend. A separate browser/API adapter may read the package only when `submission.ready=true` and the user explicitly authorizes backend work. The adapter maps fields in one batch, validates once, submits once, and immediately unpublishes the created item for human review. Do not invent a draft button or use a replacement browser session.
8. Verify the post-submit state once. If browser controls or the logged-in session fail, stop and report the concrete blocker; do not retry indefinitely or submit again.

For the layer boundaries and state transitions, read [references/architecture.md](references/architecture.md) when changing the implementation or adding a backend adapter.
For the adapter input/output boundary, read [references/backend-adapter.md](references/backend-adapter.md).

## Fixed first-version fields

- Title language: Chinese. Overseas display is handled by the storefront language switch.
- Brand: `Carlidana`.
- Category: use the confirmed jewelry style/category vocabulary; new terms are reported as `new_keywords` for review.
- Vocabulary mode: open and extensible. Do not stop or discard a title merely because a term is absent from the confirmed vocabulary; preserve the source term, record it in `new_keywords` with `keyword_sources`, and ask for confirmation separately. Only explicit forbidden terms or risk gates block.
- Price: fill the independent-store sale price with the ERP basic sale price. Leave original price blank.
- Shipping template: leave blank in version 1 and remind the reviewer to fill it after the template is imported.
- Upload exactly six images, in this order: one model image, three scene images, one main image, one size image.
- Product detail and gallery use the same six-image order. For version-1 multi-SKU work, do not automate; the later rule may use only the first five size images when explicitly enabled.

## Hard stops and safety

- Missing main image, size image, or incomplete size facts => write the warning, create the review record if possible, and do not open or submit the backend form.
- Missing model/scene images alone is not a hard stop and does not block product-data/title/risk checks; mark them as pending补图 and wait for reuse or authorized generation before final six-image submission.
- Risk evaluation uses deterministic rules plus a human-review gate. Ordinary letters, crosses, hearts, skulls, chains, and basic geometry are not automatically treated as infringement. A suspected brand imitation, brand mark, or distinctive protected design is marked for human review; unresolved or prohibited risk blocks final title generation and submission.
- Do not claim natural stone, plating, purity, solid gold, authorization, exclusivity, or patent safety without evidence. If data says `18K` but material is absent, keep it as an input keyword only and mark material confirmation when needed.
- Never modify, rename, move, or delete files in the source product library. Only copy source images into the writable review package; generated images may be added there.
- Do not put API keys, cookies, browser caches, or private configuration in the skill or review package.
- Treat the versioned review package as the handoff contract between local preparation and any backend adapter. Adapters must only map fields and perform backend I/O; they must not recompute titles, risk, tags, prices, hard gates, or image order. Replacing a backend therefore requires replacing only its adapter.

## Output

Always preserve the machine-readable package and the human-readable checklist. The package must include `status`, `risk_summary`, `risk_review`, `new_keywords`, `notes`, title candidates, selected fields, image order, warnings, and the next action. See [references/package-contract.md](references/package-contract.md).

## Optional deterministic helper

Use `scripts/auto_listing.py` to read JSON/Excel and create the package without an LLM. It accepts `--config`, `--source-root`, `--source-product-dir`, `--asset-dir`, `--keyword-config`, `--image-index`, `--review-root`, and `--generation-mode`; pass the paths for the current computer. It does not submit the backend form. `--generation-mode` defaults to `rules-only` and never calls an image service.

Use `scripts/validate_package.py` as the read-only gate inside any browser/API adapter. It validates the package contract and `submission.ready`; it does not recompute or modify package fields.

Use `scripts/record_backend_result.py` after an authorized adapter run to append the backend response to the audit log without changing the preparation package's business fields.

Use `scripts/build_image_index.py` once per library or after a material change. It scans the read-only library and writes a JSON index; daily runs can pass `--image-index` through the config to avoid rescanning.

After human review, use `scripts/promote_keywords.py` to add selected `new_keywords` into a writable vocabulary JSON. Use `--confirm 词语...` for a selected set or `--confirm-all` only when every candidate in the supplied package(s) has been reviewed. The helper creates a timestamped backup and refuses terms already listed as forbidden.
