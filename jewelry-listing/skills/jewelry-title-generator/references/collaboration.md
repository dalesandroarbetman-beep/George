# Shared Improvement Guidance

## Goal

Multiple agents can improve the title Skill while keeping one reviewed canonical version in the George repository.

## Two levels of change

1. **Case feedback** — a single product result, correction, or new candidate word. This does not change the Skill. Return it as `rule_feedback` and, when a writable feedback area is explicitly provided, save one proposal file there.
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

## Branch and pull-request workflow

1. Pull the latest George `main` and note the Skill commit in the proposal.
2. Create a focused branch such as `skill-feedback/title-20260914-rfb001`.
3. Make the smallest change needed. Keep unrelated workflow, product data, images, and local configuration out of the branch.
4. Add before/after examples and a regression check showing that existing risk stops and title constraints still work.
5. Open a pull request for review. Merge only after the maintainer confirms the rule; then agents pull the new `main` commit before future use.

If GitHub write access is unavailable, return the proposal JSON and the suggested patch text to the maintainer instead of attempting repeated pushes.
