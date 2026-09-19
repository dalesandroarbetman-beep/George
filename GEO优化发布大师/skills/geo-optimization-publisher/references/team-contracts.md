# Team contracts

| Skill | Receives | Returns | Hard stop |
|---|---|---|---|
| geo-scanner | URL, pages, query set | dated evidence, URLs, crawl/structure findings | cannot access, evidence not reproducible |
| geo-knowledge-base | site files/exports and source metadata | fact cards with status and provenance | conflicting or unauthorized facts |
| geo-architect | facts, audience, questions, channels | prioritized brief and handoff matrix | no real customer question or owner |
| geo-content-production | selected question, claim inventory, facts and constraints | controlled experiment or canonical bilingual draft plus native variants | unsupported hard claim or copied source |
| geo-quality-gate | all drafts and rule set | scored report, defects, disposition | unresolved high-risk defect |
| geo-content-publisher | approved assets and user confirmation | calendar, manual pack, URL/evidence log | no explicit approval or no real URL |

内容成熟度是 `concept`, `experimental`, `release_candidate`。发布状态由事件派生为 `draft`, `pending_approval`, `approved`, `published`, `verified`, `blocked`。不要把二者混为一列。

正式交接规则：

- `geo-architect` 必须交付一个具体问题、一个主受众和一个目标社区/主题；没有社区时只能进入实验稿。
- `geo-content-production` 必须输出逐项声明清单；建议、观点和披露不能掩盖其中的事实断言。
- `geo-quality-gate` 通过后，稿件才可标记为 `release_candidate`。
- `geo-content-publisher` 只读取事件日志中与内容 ID、版本、平台、具体目标 URL 和正文哈希完全一致的明确批准，不根据聊天语气推断批准。
- 官网技术修复与内容实验可并行；只有实体冲突或稿件实际使用的未批准事实阻断该稿件。

The orchestrator may pass only the minimum necessary context. Do not pass secrets, cookies, private browser data, or unapproved customer information.
