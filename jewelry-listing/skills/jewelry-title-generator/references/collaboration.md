# Shared Improvement Guidance

## Goal

Multiple agents can improve the title Skill while keeping one reviewed canonical version in the George repository.

## Member conversation-log mode

Normal title generation is silent about collaboration. Do not create a feedback record for every product. Only note an improvement in the current conversation when a user corrects the result, the agent finds a repeatable error, a new keyword is genuinely useful, or a risk decision is disputed. A single sentence is enough.

Suggested short form:

`改进建议｜案例: <SKU/匿名编号>｜问题: <关键词/材质/风险/格式>｜事实: <证据>｜建议: <改什么>｜置信度: <低/中/高>`

At the end of the day, the member asks `汇总今日优化日志`. The agent returns a short Chinese report that can be copied to the maintainer:

```text
饰品标题 Skill 当日优化日志
日期：YYYY-MM-DD
Skill版本：<Git提交号，如可见>

一、用户明确修正
- <案例>｜<原结果> → <用户确认结果>

二、待维护者确认
- <案例>｜问题：<关键词/材质/风险/格式>｜事实：<证据>｜建议：<改什么>｜置信度：<低/中/高>

三、重复出现的问题
- <问题>｜出现次数：<数量>｜涉及案例：<编号>

四、今日结论
- <今日无规则改进，或需要维护者重点审核的事项>
```

The report must summarize only the current conversation's available context. It must not imply access to other members' chats, private tasks, hidden logs, or GitHub history. Omit secrets, cookies, private URLs, customer information, and source images; use SKU or an anonymized case id.

## Two levels of change

1. **Case feedback** — a single product result, correction, or new candidate word. This does not change the Skill. Return `rule_feedback` only when a feedback trigger occurs; otherwise keep it empty or omit it.
2. **Canonical rule change** — a change to `SKILL.md`, a reference, or the confirmed vocabulary. This requires a separate branch, a focused pull request, and human review.

## Proposal schema

```json
{
  "feedback_id": "RFB-YYYYMMDD-XXX",
  "skill_version": "git commit or tag",
  "case_id": "SKU or anonymized case id",
  "input_mode": "image|sku|mixed",
  "problem_type": "keyword|category|style|material|risk|format|other",
  "observed_result": "what the Skill produced or missed",
  "evidence": "资料字段、图片可见事实或用户修正",
  "proposed_change": "具体规则或词形调整",
  "confidence": "low|medium|high",
  "user_confirmed": false
}
```

Do not place secrets, cookies, private URLs, customer information, or source images in a proposal. Refer to a SKU or an anonymized case id instead.

## Promotion thresholds

- New keyword: remains an open candidate until explicit user/maintainer confirmation.
- Wording, ordering, or omission rule: promote only after two independent cases or explicit user approval.
- Risk/IP gate: promote only after explicit human review; never infer a global risk rule from one ambiguous image.

## Maintainer review workflow

The maintainer receives daily reports from members and performs the only canonical update. Reports can be combined, deduplicated, and counted without requiring members to touch GitHub. The maintainer may ask an agent to review a specified set of past task conversations, but this is opt-in and scoped; do not scan or copy private conversations by default.

## Canonical update workflow

Only the maintainer changes the canonical Skill or vocabulary. The maintainer should pull the latest George `main`, make the smallest focused change, run the Skill validator, and push or merge according to the repository's normal review policy. Members do not need GitHub write access.

If the maintainer wants a formal review, the maintainer may still use a separate branch and Pull Request; this is not a requirement for members' daily logs.
