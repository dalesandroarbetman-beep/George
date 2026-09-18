# Team contracts

| Skill | Receives | Returns | Hard stop |
|---|---|---|---|
| geo-scanner | URL, pages, query set | dated evidence, URLs, crawl/structure findings | cannot access, evidence not reproducible |
| geo-knowledge-base | site files/exports and source metadata | fact cards with status and provenance | conflicting or unauthorized facts |
| geo-architect | facts, audience, questions, channels | prioritized brief and handoff matrix | no real customer question or owner |
| geo-content-production | approved brief and fact cards | master draft, native platform drafts, sources | unsupported claim or copied source |
| geo-quality-gate | all drafts and rule set | scored report, defects, disposition | unresolved high-risk defect |
| geo-content-publisher | approved assets and user confirmation | calendar, manual pack, URL/evidence log | no explicit approval or no real URL |

State values: `draft`, `pending`, `ready`, `queued`, `approved`, `published`, `verified`, `blocked`.

The orchestrator may pass only the minimum necessary context. Do not pass secrets, cookies, private browser data, or unapproved customer information.
