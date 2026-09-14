# 上品包合同

## 目录

```text
复审和备份/
└── 批次/
    └── 货号/
        ├── 上品包.json
        ├── 审核清单.md
        └── 图片/
            ├── 货号-模特图.jpg
            ├── 货号-场景图1.jpg
            ├── 货号-场景图2.jpg
            ├── 货号-场景图3.jpg
            ├── 货号-主图.jpg
            └── 货号-尺寸图.jpg
```

## JSON 必备字段

```json
{
  "sku": "string",
  "status": "可上架|资料冲突待确认|材质待确认|品牌/IP风险待确认|风险无法确认|PASS/禁止上架",
  "risk_summary": "string",
  "title": "string|null",
  "title_options": ["string"],
  "brand": "Carlidana",
  "category": "string",
  "tags": ["string"],
  "sale_price": "number|null",
  "original_price": null,
  "shipping_template": null,
  "image_order": ["path"],
  "detail_images": ["path"],
  "warnings": ["string"],
  "new_keywords": ["string"],
  "notes": ["string"],
  "next_action": "string"
}
```

图片不齐全时仍保存上品包和审核清单，但 `next_action` 必须是补资料/人工复核，不能写成可提交。审核清单必须提醒运费模板后续补填，以及创建成功后立即下架等待人工审核。
