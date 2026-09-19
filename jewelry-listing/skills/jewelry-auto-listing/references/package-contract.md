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
  "contract_version": "1.2",
  "sku": "string",
  "run_id": "批次/货号",
  "processed_at": "ISO-8601 timestamp",
  "review_dir": "string",
  "missing_images": ["model|scene1|scene2|scene3|main|size"],
  "creative_mode": "rules-only|external-optional",
  "status": "可上架|资料冲突待确认|材质待确认|品牌/IP风险待确认|风险无法确认|PASS/禁止上架",
  "risk_summary": "string",
  "risk_review": {
    "method": "规则初筛+人工复审",
    "decision": "规则初筛通过，保留人工复审入口|人工复审",
    "manual_review_required": false,
    "basis": "string",
    "generic_elements_not_auto_flagged": ["string"]
  },
  "title": "string|null",
  "title_options": ["string"],
  "brand": "Carlidana",
  "category": "string",
  "tags": ["string"],
  "sale_price": "number|null",
  "original_price": null,
  "shipping_template": null,
  "size_facts": {
    "specification": "string",
    "length": "string",
    "weight": "string",
    "length_confirmed": true,
    "weight_confirmed": true,
    "complete": true,
    "missing": []
  },
  "image_order": ["path"],
  "detail_images": ["path"],
  "warnings": ["string"],
  "new_keywords": ["string"],
  "keyword_sources": {"词语": "商品资料/字段|图片判断|人工确认|历史候选"},
  "notes": ["string"],
  "workflow_stage": "string",
  "hard_stops": ["string"],
  "submission": {
    "ready": false,
    "blocked_reasons": ["string"],
    "action": "create_then_unpublish|review_only",
    "adapter_rule": "只读取本上品包并映射字段；不得重新计算标题、风险、标签或图片顺序"
  },
  "backend_result": null,
  "source": {
    "source_root": "string",
    "source_product_dir": "string|null",
    "asset_dir": "string|null",
    "image_index": "string|null"
  },
  "next_action": "string"
}
```

图片不齐全时仍保存上品包和审核清单。缺主图、尺寸图、长度字段或重量字段必须进入 `hard_stops`，`next_action` 必须是补资料/人工复核；仅缺模特图或场景图时写入 `warnings` 的“待补素材（不影响资料检查）”，不得把它们当作资料冲突，但在六张图补齐前不能提交后台。审核清单必须提醒运费模板后续补填，以及创建成功后立即下架等待人工审核。

人工确认新词时，使用 `scripts/promote_keywords.py` 读取一个或多个上品包；工具只写入词库 JSON，并为已有词库创建时间戳备份，不修改上品包和原始货盘。

每次运行使用不重复的 `run_id` 和批次目录，重复处理同一货号不会覆盖历史批次。`处理日志.jsonl` 追加记录处理时间、状态、缺失图片、风险判断和 `backend_result`；准备阶段的后台结果为 `null`，后台适配器完成后使用 `scripts/record_backend_result.py` 追加结果。日志采用追加写入，不覆盖历史记录。

## 后台适配器边界

上品程序只负责生成完整上品包，不访问后台、不填写表单。浏览器适配器和 API 适配器是独立组件：先读取 `contract_version`、`submission.ready`、`blocked_reasons`，只有 `ready=true` 才能执行字段映射和提交；提交后按后台能力立即下架并回写结果。适配器不得重新计算标题、风险、标签、价格、图片顺序或硬闸门，也不得修改原始货盘。更换后台时只新增或替换适配器，不修改前面的资料、规则和上品包生成程序。
