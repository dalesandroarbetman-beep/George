# Auto-listing Data Contract

## Input

```json
{
  "sku": "string",
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

Missing fields are valid. Do not fill them with guesses merely to satisfy the schema.

## Output

```json
{
  "sku": "string",
  "status": "可上架|资料冲突待确认|材质待确认|品牌/IP风险待确认|风险无法确认|PASS/禁止上架",
  "risk_summary": "string",
  "titles": ["string", "string", "string"],
  "unused_keywords": ["string"],
  "new_keywords": ["string"],
  "notes": ["string"]
}
```

For `风险无法确认`, `品牌/IP风险待确认`, or `PASS/禁止上架`, return an empty `titles` array. For ordinary material uncertainty, three test titles are allowed, but the status must remain visible.
