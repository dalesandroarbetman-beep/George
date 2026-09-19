# GEO优化发布大师

面向 YOHO 独立站的 GEO 内容协作项目。它将公开网站证据整理为可追溯事实卡，再以问答方式生成适合 Reddit、Quora、Indie Hackers 的英语内容，并可派生 X、LinkedIn、Facebook 版本。所有用户审核文件使用中文，或英文原文附完整中文翻译。

## 项目目标

- 通过持续发布有用、可核验、符合平台语境的英文回答，提升 `https://www.yohodiy.com/` 的搜索可见性与权威信号。
- 服务三类海外受众：女性时尚爱好者、批发商、独立站饰品销售商。
- 使用人工审核、人工发布和真实 URL 留痕；不自动登录或发帖。
- 不承诺搜索排名、收录、引用、外链存活或流量结果。

## Skill 团队

| Skill | 职责 |
|---|---|
| `geo-optimization-publisher` | 总控、渐进式问答、阶段状态与交接 |
| `geo-scanner` | 只读扫描公开站点与可复现证据 |
| `geo-knowledge-base` | 生成带来源、状态和冲突记录的事实卡 |
| `geo-architect` | 规划受众、问题矩阵、内容集群与平台顺序 |
| `geo-content-production` | 生成受控探索稿或有事实依据的正式双语审核稿 |
| `geo-quality-gate` | 检查事实、逻辑、说人话、披露、平台语气和打包一致性 |
| `geo-content-publisher` | 生成审批队列、人工发布包与真实 URL 记录 |

## 已确认规则

- 对外英文品牌统一为 `YOHO`。
- 唯一对外来源与 CTA 域名为 `https://www.yohodiy.com/`。
- 法律主体信息保留在事实卡中，不在论坛文案中主动强调。
- 三条内容方向全部纳入长期计划：个性化珠宝、批发/采购、独立站饰品销售。
- 单篇内容只选择一个主要问题、一个主受众和一个自然的读者下一步。
- 网站上出现的价格、时效、物流、材质、证书、比例和效果数据必须单独批准后才能成为外部硬断言。
- 内容成熟度与发布状态分开；允许受控试写，不允许把探索稿当成正式待发布稿。
- 人工决定写入追加式事件日志，当前状态由工具自动生成。

## 工作流

```text
核心问答
  -> 网站证据与知识库
  -> 问题矩阵和内容架构
  -> 逐项声明分类与最小事实批准
  -> 受控探索稿或规范母稿
  -> Reddit / Quora / Indie Hackers 双语审核版本
  -> 质量审查
  -> 正式候选稿
  -> 人工批准
  -> 带 SHA-256 的发布包
  -> 人工发布
  -> 真实 URL 与效果复盘
```

当前已建立 41 张待审事实卡和三篇 `experimental` 双语试稿。品牌、法律主体披露策略、规范来源域名、人工发布和自然语气规则已经确认；首篇正式内容仍需选择具体社区/主题。

## 目录

```text
GEO优化发布大师/
|-- README.md
|-- AGENTS.md
|-- requirements.txt
|-- tests/
|-- skills/
|   |-- geo-optimization-publisher/
|   |-- geo-scanner/
|   |-- geo-knowledge-base/
|   |-- geo-architect/
|   |-- geo-content-production/
|   |-- geo-quality-gate/
|   `-- geo-content-publisher/
`-- output/
    |-- geo-scan/yohodiy-20260918/
    |-- geo-program/yohodiy-20260918/
    `-- site-knowledge/yohodiy-knowledge-base-20260918/
```

## 验证

项目根目录下运行：

```text
python skills/geo-optimization-publisher/scripts/geo_workflow.py --project-root . validate
python skills/geo-optimization-publisher/scripts/geo_workflow.py --project-root . status --json-out output/geo-program/yohodiy-20260918/workflow_status.json --md-out output/geo-program/yohodiy-20260918/workflow_status.md
python -m unittest discover -s tests -p "test_*.py"
```

审核 ZIP 使用 `package --mode review --content-id <ID>`；`package --mode publish --content-id <ID>` 会拒绝探索稿、缺少具体目标 URL 的稿件，以及批准事件与版本、平台、目标或正文哈希不一致的内容。两种模式都不会执行真实发布。

## 数据边界

仓库只保存公开、经过筛选的知识库摘要与工作流代码。不提交账号、Cookie、密钥、订单、支付、用户数据、浏览器缓存或 `.env` 文件。
