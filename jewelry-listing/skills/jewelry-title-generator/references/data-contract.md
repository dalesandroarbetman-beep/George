# Auto-listing Data Contract

## Input

```json
{
  "sku": "string|null",
  "product_data": {
    "name": "string|null",
    "category": "string|null",
    "series": "string|null",
    "style": "string|null",
    "shape": "string|null",
    "finish": "string|null",
    "material": "string|null",
    "decoration": "string|null",
    "color": "string|null",
    "specification": "string|null",
    "tags": ["string"]
  },
  "images": ["path-or-image-reference"],
  "user_confirmed_fields": ["string"]
}
```

`images` may be the only populated input. Missing fields are valid. Do not fill them with guesses merely to satisfy the schema. If the user sends an image without an SKU, use `sku: null` in machine-readable output and display `未提供SKU` in the human response. Record image-derived fields in `notes` or `keyword_sources`.

## Output

```json
{
  "sku": "string|null",
  "status": "可上架|资料冲突待确认|材质待确认|品牌/IP风险待确认|风险无法确认|PASS/禁止上架",
  "risk_summary": "string",
  "titles": ["string", "string", "string"],
  "unused_keywords": ["string"],
  "new_keywords": ["string"],
  "notes": ["string"],
  "rule_feedback": []
}
```

For `风险无法确认`, `品牌/IP风险待确认`, or `PASS/禁止上架`, return an empty `titles` array. For ordinary material uncertainty, three test titles are allowed, but the status must remain visible.

`rule_feedback` is optional for ordinary cases and contains zero or more proposals using the schema in [collaboration guidance](collaboration.md). A proposal records a possible improvement only; it does not authorize an automatic change to this Skill or its confirmed vocabulary.
