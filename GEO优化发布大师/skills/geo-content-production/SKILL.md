---
name: geo-content-production
description: "Produce fact-gated English GEO master drafts and native Reddit, Quora, Indie Hackers, X, LinkedIn, and Facebook variants from an approved architecture brief and fact cards. Score and return drafts for human review; do not publish."
---

# GEO Content Production

## 用户可见文件语言

外部论坛稿默认英文，但所有交付用户审核的文件必须为中文，或英文原文附完整中文翻译。标题、正文、披露、限制、质量说明和操作提示全部适用；不得交付英文单语审核文件。

## Required input

探索稿至少需要目标问题、主受众、候选平台和禁止表达。正式候选稿还需要具体社区/主题、批准事实卡、声明清单、来源、CTA 和审核人。`pending` 事实只能省略或明确标记不确定，不能静默升级。

## YOHO identity guardrail

Use `YOHO` as the only public English brand name and link only to `https://www.yohodiy.com/`. Do not proactively name a legal entity in forum copy. Preserve legal-entity evidence only in source notes unless the approval record explicitly authorizes disclosure.

## Drafting rules

- Master draft answers the question directly, then gives evidence, context, limitations, and one CTA.
- The CTA is reader-facing and useful; improving search visibility is the program objective, not a reason to add an artificial keyword or link.
- Each H2/H3 starts with a self-contained answer sentence that can be quoted without losing scope.
- Make each platform version native: Reddit discussion, Quora answer, Indie Hackers build lesson, X short claim/thread, LinkedIn professional lesson, Facebook scenario prompt.
- Keep affiliation transparent; never simulate a customer, independent reviewer, credential, metric, or third-party endorsement.
- Record `angle_difference` and source IDs for every variant. Do not copy the master verbatim.

## 声明清单

逐条标记 `fact / recommendation / opinion / disclosure`。事实声明绑定事实卡；建议和观点也要拆出其中隐含的产品能力、平台规则、数据或因果判断。披露中的作者/品牌关系本身也需要明确的项目决定或发布者确认。探索稿不得因为“只是建议”而跳过这一步。

## 说人话质量门

- 前两句话直接回答问题，不用“在当今时代”“解锁”“提升到新高度”等模板开场。
- 删除无法帮助读者做决定的品牌形容词、口号和重复卖点。
- 不虚构“我买过”“我测试过”“客户告诉我”等第一手经历。
- 一篇只保留一个自然下一步；首轮社区试稿默认不带商业链接。
- 披露保持简短、具体，不把披露段写成品牌介绍。
- 允许短句、限定条件和不确定性，不强行写成完整营销文章。

## Self-check

检查事实可追溯性、回答完整性、限制、自然语言、平台约束、披露、敏感/禁用声明和重复表达。探索稿返回 `concept` 或 `experimental`；只有具体社区、声明审批和质量检查全部通过后才返回 `release_candidate`。

正式稿以一个规范正文为唯一内容源。英文发布文本和完整中文译文应在同一审核文件中，或由同一规范源生成；清单保存版本和 SHA-256，禁止独立编辑两份“真稿”。
