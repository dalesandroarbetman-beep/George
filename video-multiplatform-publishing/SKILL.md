---
name: video-multiplatform-publishing
description: "Generate platform-native launch plans for a product short video across TikTok, Instagram Reels, YouTube Shorts, Facebook, X, and DIY channels, with bilingual copy, hashtags, posting settings, UTM links, comment prompts, and follow-up metrics. Use when a user asks to turn a product video into a multi-platform publishing plan; do not use for actually posting content."
metadata:
  short-description: "Create bilingual six-platform video plans"
---

# Video Multiplatform Publishing

Turn one product short video into a practical, platform-native publishing plan for six destinations:
TikTok, Instagram Reels, YouTube Shorts, Facebook, X (Twitter), and a DIY or making-focused account.

## Workflow

1. Inspect the supplied video or the available keyframes. Record only observable facts: duration, aspect ratio, narrative beats, product features shown, filming technique, on-screen text, and content form (展示型, 开箱型, 制作过程型, 口播型, or 选择仪式型). Infer C-end or B-end intent separately and label the inference.
2. If the video cannot be inspected, request keyframes or a concise scene description. Do not invent product materials, dimensions, prices, availability, certifications, or performance claims.
3. Read [references/platform-playbook.md](references/platform-playbook.md) for channel-specific decisions and [references/output-template.md](references/output-template.md) for the required Markdown structure.
4. Write native copy for each platform rather than cloning one caption. Every platform needs a primary English caption with a Chinese translation, an alternate angle, 5–10 relevant hashtags, and posting settings.
5. Keep the conversion path consistent: use the supplied profile link or a clearly marked placeholder and the CTA text `Link in bio`. Do not imply a shopping-cart or checkout integration that the user did not provide. Recommend removing download watermarks when the source workflow supports it.
6. Add a UTM link matrix, 6–8 bilingual comment/reply prompts, and a 48–72 hour observation and series-reuse plan.
7. Distinguish facts, inferences, and recommendations in the analysis. Treat timing, boost, BGM, and audience guidance as heuristics; state the assumed timezone and audience when they are not supplied.

## Fixed output

Use the ten-section order in the output template:

`一、视频分析` → `二、TikTok` → `三、Instagram Reels` → `四、YouTube Shorts` → `五、Facebook` → `六、X` → `七、DIY 垂类账号` → `八、UTM 链接矩阵` → `九、评论区运营话术` → `十、发布节奏与检查清单`.

The final document is an execution draft, not a guarantee of reach or sales. Keep the tone native and human, avoid inflated advertising language, and preserve Chinese translations as working notes for overseas publishing.

## Boundaries

- This skill drafts and audits publishing plans; it does not publish, boost, scrape, or log in to social platforms.
- Do not include user videos, audio, credentials, `.env.local`, browser caches, or private configuration in project artifacts or Git.
- Public platform facts may be used, but do not bypass login, regional restrictions, or anti-bot controls.
- Summarize and transform third-party copy; do not reproduce a complete third-party caption or script.
