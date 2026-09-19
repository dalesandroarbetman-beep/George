# GEO优化发布大师

面向 YOHO 独立站的 GEO 内容协作项目。它将公开网站证据整理为可追溯事实卡，再以问答方式生成适合 Reddit、Quora、Indie Hackers 的英文内容，并可派生 X、LinkedIn、Facebook 版本。

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
| `geo-content-production` | 生成英文母稿及平台原生版本 |
| `geo-quality-gate` | 检查事实、逻辑、披露、平台语气和风险 |
| `geo-content-publisher` | 生成审批队列、人工发布包与真实 URL 记录 |
| `mingjingmen` | 对复杂答案和改写稿进行独立批判审查 |
| `text-to-pdf` | 将中文审核材料排版为 HTML/PDF；依赖 Chromium、Playwright 或 WeasyPrint |

## 已确认规则

- 对外英文品牌统一为 `YOHO`。
- 唯一对外来源与 CTA 域名为 `https://www.yohodiy.com/`。
- 法律主体信息保留在事实卡中，不在论坛文案中主动强调。
- 三条内容方向全部纳入长期计划：个性化珠宝、批发/采购、独立站饰品销售。
- 单篇内容只选择一个主要问题、一个主受众和一个自然的读者下一步。
- 网站上出现的价格、时效、物流、材质、证书、比例和效果数据必须单独批准后才能成为外部硬断言。

## 工作流

```text
核心问答
  -> 网站证据与知识库
  -> 问题矩阵和内容架构
  -> 事实批准
  -> 英文母稿
  -> Reddit / Quora / Indie Hackers 原生版本
  -> 质量审查
  -> 人工批准
  -> 人工发布
  -> 真实 URL 与效果复盘
```

当前已建立 41 张待审事实卡。品牌、法律主体披露策略和规范来源域名已经确认；首篇具体问题、对应事实卡和读者 CTA 仍待选择。

扫描和发布数据分别由 `contracts/geo-scan-v1.schema.json` 与 `contracts/geo-publish-pack-v1.schema.json` 约束。扫描器只读取公开页面；发布器只生成本地人工执行包，`--dry-run` 不会登录或发帖。

## 目录

```text
GEO优化发布大师/
|-- README.md
|-- AGENTS.md
|-- requirements.txt
|-- skills/
|   |-- geo-optimization-publisher/
|   |-- geo-scanner/
|   |-- geo-knowledge-base/
|   |-- geo-architect/
|   |-- geo-content-production/
|   |-- geo-quality-gate/
|   `-- geo-content-publisher/
`-- output/
    |-- geo-program/yohodiy-20260918/
    `-- site-knowledge/yohodiy-knowledge-base-20260918/
```

## 验证

使用 Codex 的 `skill-creator/scripts/quick_validate.py` 验证每个 Skill，并用 Python 编译检查知识库脚本。抓取依赖见 `requirements.txt`。

仓库根目录可统一运行：

```powershell
python -X utf8 tools/run_project_checks.py
```

## 数据边界

仓库只保存公开、经过筛选的知识库摘要与工作流代码。不提交账号、Cookie、密钥、订单、支付、用户数据、浏览器缓存或 `.env` 文件。
