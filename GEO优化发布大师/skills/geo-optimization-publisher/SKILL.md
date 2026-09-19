---
name: geo-optimization-publisher
description: "GEO优化发布大师：以问答方式把独立站事实转成 Reddit、Quora、Indie Hackers 原生内容，并派生 X、LinkedIn、Facebook 等英文版本；协调扫描、知识库、架构、内容生产、质量审查和人工发布，不自动代发。适用于 GEO 内容规划、论坛文案、跨平台改写和发布执行包。"
---

# GEO优化发布大师

这是一个总控 Skill，不是单纯的文案生成器。它协调扫描、事实卡、选题、写作、审查和人工发布，保证“事实先于硬断言、探索稿与正式稿分开、人工批准后发布”。外部平台稿默认英文；凡交付给用户查看的文件，必须是中文，或英文原文附完整中文翻译。

## 团队分工

- `geo-scanner`：只读检查官网、站外实体、可引用证据和当前 GEO 基线。
- `geo-knowledge-base`：把独立站资料整理为有来源、有状态、有版本的事实卡；知识库未就绪时先建立导入接口。
- `geo-architect`：确定目标问题、受众、优先级、平台组合、内容资产和阶段闸门。
- `geo-content-production`：生成受控探索稿，或从批准事实卡生成英文母稿和平台原生变体。
- `geo-quality-gate`：执行事实、逻辑、平台语气、反营销、重复度和合规审查；高价值内容可调用 `mingjingmen` 做一轮独立批判。
- `geo-content-publisher`：生成日历、人工审批清单、发布执行包、URL 留痕和复盘记录；不自动登录或发帖。

## 默认目标

- 论坛：Reddit、Quora、Indie Hackers。
- 派生平台：X、LinkedIn、Facebook；用户指定平台优先。
- 语言：外部平台内容默认英文；用户可见报告、草稿、审核单、执行包和说明必须为中文，或英文原文附完整中文翻译。
- 发布：人工操作。没有用户逐条确认，不进入 `approved` 或 `published`。
- 项目目标：通过持续发布有用、可追溯、平台原生的英文回答，提升独立站的搜索可见性与权威信号；不承诺排名、收录、引用或流量结果。
- 知识库：首版默认从 `https://www.yohodiy.com/` 的公开渲染页面抓取；后续仍可补充 Markdown、Word、PDF、表格或数据库导出。所有抓取内容先进入事实卡，不直接当成已批准事实。

## 已确认的身份与来源策略

- 对外英文品牌统一写作 `YOHO`。站内出现的 `YOHE/YOUNG`、`Yoho Origin`、`YOHO DIY` 只作为事实卡中的原始别名和冲突证据保存，不在论坛稿中混用。
- 论坛文案暂不主动强调法律主体；法律实体信息保留在事实卡，只有用户逐条批准时才可进入发布包。
- 外部文案、引用和 CTA 统一使用 `https://www.yohodiy.com/`。`diy.lsdit.com` 只能作为抓取证据中的候选主机，不作为对外链接。
- 品牌身份策略已解决不等于产品能力、价格、时效、物流、资质或效果已批准；这些仍必须经过事实卡闸门。

## 渐进式问答

首次启动只问会改变整体方向的核心问题，不一次性索要所有细节。已有答案不重复问；能从已批准项目决定中确定的内容不再询问。

核心问题：

1. 本轮优先服务哪一类受众、回答哪个真实问题？
2. 首发平台和具体社区/主题是什么？
3. 本篇允许使用哪些事实卡，哪些内容明确不能说？
4. 读者看完后最自然的下一步是什么？

第二轮再询问语气、披露位置、素材、发布时间、负责人和测量方式。缺失信息标为 `pending`，不得猜测。三类受众都纳入长期计划，但单篇内容只选择一个主受众。

## 标准流水线

`core_questions → crawl/scan → fact_cards → question_selection → claim_inventory → controlled_draft → quality_gate → release_candidate → human_approval → review_package → manual_publish → evidence_log → review`

探索性写作与正式发布分开：缺少具体社区时，可以继续生成明确标记为 `concept` 或 `experimental` 的无外发风险草稿；必须暂停升级为 `release_candidate` 或发布包。审核包可用于内部决策，但必须标记 `publishable=false`。只有稿件实际使用事实声明时才要求对应事实卡批准；实体冲突、未批准硬断言或未解决的高风险问题会阻断正式稿。

## 两层状态模型

- 内容成熟度：`concept → experimental → release_candidate`。成熟度描述稿件用途，不证明已经获批。
- 发布状态：由追加式事件日志自动派生为 `draft → pending_approval → approved → published → verified`；任何阶段都可因明确原因成为 `blocked`。

不要手工维护另一份“当前状态真相”。`workflow_manifest.json` 保存内容元数据，`approval_events.jsonl` 只追加决定和外部事件，`workflow_status.json/.md` 由脚本生成。

## 母稿与版本原则

- 正式稿以一个规范正文为唯一内容源；英文发布文本和中文审核译文保存在同一文件，或由同一源生成，并用版本号和 SHA-256 绑定。
- 每条声明分类为 `fact / recommendation / opinion / disclosure`。`fact` 必须绑定已批准事实卡；不能因为整篇属于“建议型内容”就绕过事实闸门。
- Reddit 版本优先真实问题、经验边界和评论互动；不得伪装普通用户或隐瞒商业关系。
- Quora 版本优先直接回答、定义、步骤、限制和可核验来源；避免广告腔。
- Indie Hackers 版本优先产品构建、实验、取舍、失败和可复用经验；不得把销售页改名为故事。
- X、LinkedIn、Facebook 只做平台原生重写，不复制论坛原文；记录每版与母稿的角度差异。
- 外部论坛不能制造独立背书；只能使用真实、公开、可追溯的事实。
- “说人话”是质量门：开头直接回答，删除口号、模板化营销词、虚假经历、堆叠卖点和多重 CTA；披露简短自然，品牌只在回答确有必要时出现。

## 发布边界

本 Skill 只生成草稿、评分单、审核包、人工发布执行包和留痕模板。不得自动登录、输入验证码、提交帖子、购买广告、群发、刷量或伪造发布结果。用户明确逐条批准后，仍由用户人工完成发布；用户回传真实 URL 和时间后才可登记为 `published`。单篇试发只验证操作链路，不能据此判断渠道有效性。

## 交付物

根据任务选择最小集合：`brief.md`、`fact_cards.json`、`question_matrix.md`、`workflow_manifest.json`、`approval_events.jsonl`、双语内容稿、`quality_report.md`、`approval_queue.md`、`workflow_status.json/.md`、带哈希的审核/发布包、`evidence_log.json`、`review_note.md`。

## 参考文件

- [团队契约](references/team-contracts.md)：专项 Skill 的输入输出和状态。
- [问答表](references/questionnaire.md)：核心问题与第二轮细节问题。
- [国外平台规则](references/foreign-platform-rules.md)：Reddit、Quora、Indie Hackers、X、LinkedIn、Facebook 的适配重点。
- [输出契约](references/output-schema.md)：母稿、平台稿、审查和发布执行包字段。
- [可复现评分规则](../geo-scanner/references/scoring-rubric.md)：官网扫描分数的证据和扣分方法。
- [压缩包适配说明](references/archive-adaptation-notes.md)：六个压缩包的采用、改造和阻断项。

## 工具

在项目根目录运行 `python skills/geo-optimization-publisher/scripts/geo_workflow.py --project-root . validate`，校验事实引用、双语要求、扫描分数、事件和发布门；用 `status` 生成派生状态；用 `package --mode review|publish --content-id <ID>` 生成指定内容的带哈希 ZIP。`review` 只是审核包；`publish` 必须达到 `approved`，并再次核对版本、平台、具体目标 URL 与正文哈希。脚本不会执行真实发布。
