# Output contract

Every deliverable records:

```yaml
content_id: "..."
status: draft|pending|ready|queued|approved|published|verified|blocked
target_question: "..."
audience: "..."
approved_fact_ids: []
source_records: []
platform: "reddit|quora|indie_hackers|x|linkedin|facebook"
master_path: "..."
variant_path: "..."
angle_difference: "..."
cta: "..."
risks: []
human_approval: null
published_url: null
published_at: null
```

The master draft must include a direct answer, evidence, limitations, one CTA, and a `pending` section. Each platform file must include the platform goal, the difference from the master, disclosure note, and a manual preflight checklist.
