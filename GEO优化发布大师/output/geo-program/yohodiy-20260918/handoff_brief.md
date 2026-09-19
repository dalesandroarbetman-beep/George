# YOHO GEO 团队交接说明 v1

## 输入

- 事实卡：`output/site-knowledge/yohodiy-knowledge-base-20260918/fact_cards.json`
- 事实卡审核表：`output/site-knowledge/yohodiy-knowledge-base-20260918/fact_card_review.md`
- 内容架构：`architecture_brief.md`
- 问题矩阵：`question_matrix.md`
- 工作流清单：`workflow_manifest.json`
- 追加式决定记录：`approval_events.jsonl`

## 协作顺序

`geo-scanner → geo-knowledge-base → geo-architect → geo-content-production → geo-quality-gate → geo-content-publisher`

官网技术修复和内容实验可以并行。正式发布仍必须按上述交接顺序通过。

## 交接规则

- Scanner：返回带日期、URL、评分子项和限制的公开证据；`scan.json`、`offsite.json`、`baseline.md` 缺一不可。
- Knowledge Base：保留原始事实卡，不覆盖审批历史；人工决定写入事件日志。
- Architect：每篇选一个问题、一个主受众、一个平台和一个具体社区/主题。
- Content Production：逐项区分事实、建议、观点和披露；探索稿与正式稿隔离。
- Quality Gate：检查事实、逻辑、平台适配、说人话、披露、重复度和文件哈希；高风险问题未解决时阻断正式升级。
- Publisher：只生成审核包或人工发布包；只有明确批准事件才能生成发布包，真实 URL 只能由用户回传。

## 当前交接状态

三篇内容均为 `experimental`，可继续修改语气，但不在正式发布队列。下一次有效交接应先选择一个具体社区/主题，再只审批该稿实际使用的声明。
