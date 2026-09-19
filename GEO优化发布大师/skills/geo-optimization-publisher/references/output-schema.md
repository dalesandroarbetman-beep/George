# 输出契约

`workflow_manifest.json` 保存项目和内容元数据，但不充当人工可编辑的当前状态文件。当前发布状态由 `approval_events.jsonl` 派生。

每个内容项至少包含：

```yaml
content_id: "YOHO-..."
version: 1
maturity: concept|experimental|release_candidate
target_question: "..."
audience: "..."
platform: reddit|quora|indie_hackers|x|linkedin|facebook
community: null
target_url: null
claim_inventory:
  - claim_id: "C-001"
    type: fact|recommendation|opinion|disclosure
    text_en: "..."
    text_zh: "..."
    fact_ids: []
approved_fact_ids: []
source_records: []
master_path: null
variant_path: "..."
angle_difference_zh: "..."
angle_difference_en: "..."
cta_zh: "..."
cta_en: "..."
risks_zh: []
risks_en: []
quality_status: pending|pass|blocked
publisher_owner: null
disclosure_position: null
community_rules_checked_at: null
```

## 约束

- `concept`、`experimental` 允许 `community`、`master_path` 或事实审批为空，但不能进入正式审批或发布包。
- `release_candidate` 必须有可唯一定位的社区/问题 URL、规范母稿、逐项声明分类、发布负责人、披露位置、规则核验日期和 `quality_status=pass`。
- `fact` 声明必须引用事实卡；所引事实必须已在事实卡中验证，或由最新的 `fact_approval` 事件批准。
- 如果稿件没有 `fact` 声明，可以在不批准事实卡的情况下成为正式候选稿；但披露中的作者/品牌关系本身是事实，必须绑定明确的项目决定事件。
- 英文论坛稿必须在同一审核文件中包含完整中文翻译。正文版本和打包文件使用 SHA-256 关联。
- `published_url`、`published_at` 不写回内容稿；由用户人工发布后，通过 `publication` 事件追加。

## 事件日志

`approval_events.jsonl` 每行一个 JSON 对象，只追加不覆盖。事件类型为：

`program_decision | fact_approval | content_approval | publication | verification | block | unblock`

每条事件包含 `event_id`、`event_type`、`subject_id`、`decision`、`recorded_at`、`actor`、`details_zh`。内容批准、发布和验证事件还必须绑定 `content_version`、`platform`、`community`、`target_url` 和 `content_sha256`；发布事件另含真实 `url` 与 `published_at`。旧版本、其他平台或其他目标的批准不能复用。

## 派生状态

`experimental` 默认派生为 `draft`；合格的 `release_candidate` 派生为 `pending_approval`。只有批准事件与内容版本、平台、具体目标和正文哈希完全一致时才成为 `approved`；真实 URL 与时间记录后为 `published`；完成复核后为 `verified`。未解除的 `block` 优先显示为 `blocked`。
