---
name: text-to-pdf
description: 把文字内容转换成专业美观的 PDF。当用户提供文字(报告/分析/复盘/文章等)并希望输出为排版精良、可直接交付的 PDF 时触发。技术路线为 文字 → 结构化 HTML → Playwright(Chromium) 渲染 → PDF, 自带 WeasyPrint 兜底。当用户说"做成PDF""出个PDF报告""把这些内容排成PDF""生成美观PDF"时必须触发。
---

# text-to-pdf · 文字 → 美观 PDF

把纯文字变成咨询机构质感的 PDF。**决定美观的是模板 CSS, 不是转换工具**——agent 只负责把文字组织成结构化 HTML, 套用现成模板, 样式自动生效。

## 工作流(4 步)

1. **判型 + 结构化**: 读输入文字, 判断文档类型(报告/文章/手册…), 拆成标题、段落、表格、要点、数据卡、图表等语义块。
2. **生成内容 HTML**: 复制对应模板的 `<head>`(含 `<link rel="stylesheet" href="report.css">`), 把内容填进 `<body>`, 使用下方约定的 class。**HTML 必须和模板 CSS 同目录**(或正确设置相对路径), 否则样式不生效。
3. **样式自动**: 不要手写/改 CSS, 直接复用模板。需要新风格时另起模板, 不污染现有的。
4. **转 PDF + 自检**: 调 `html2pdf.py`, 然后**转图肉眼检查**(见自检清单)。

## 可用模板(4 种风格)

| 风格 | 适用 | 转换 margin / footer(务必照用) |
|---|---|---|
| `report` 咨询蓝 | 商业/分析报告、复盘 | `--margin "20mm 17mm 18mm 17mm"`(默认, 带页脚页码) |
| `editorial` 杂志红 | 深度长文、观点、方法论 | `--margin "22mm 24mm 22mm 24mm"` |
| `tech` 科技青 | AI 产品、技术白皮书、数据报告 | `--margin "0 0 0 0" --no-footer`(满版深色) |
| `warm` 暖橙 | 培训招生、活动一页纸 | `--margin "0 0 0 0" --no-footer`(满版浅色) |

每种都带完整示例; 仿写时直接读对应 `templates/<风格>.html` 学结构与 class。

## report 模板 · 内容 class 速查

| 区块 | 写法 |
|---|---|
| 封面 | `<section class="cover">` 内含 `.eyebrow` / `<h1>` / `.sub` / `.accent-bar` / `.meta` |
| 章节标题 | `<h2><span class="num">01</span>标题</h2>` |
| 子标题 | `<h3>标题</h3>`(自动带青色竖条) |
| 执行摘要 | `<div class="summary"><span class="label">…</span>正文</div>` |
| 数据卡行 | `<div class="kpi-row">` 内多个 `.kpi`(含 `.val`/`.key`/`.delta .up\|.down`) |
| 表格 | 标准 `<table>`, 数字列加 `class="num"` 右对齐 |
| 图表 | 内联 `<svg>` 放进 `<div class="chart">`, 配 `.cap` 图注 |
| 结论框 | `<div class="takeaway">`(深色底, 内部文字自动转白) |
| 脚注 | `<p class="note">…</p>` |

## 转换命令

```bash
# margin 按上表对应风格填; tech/warm 还需 --no-footer
python3 scripts/html2pdf.py <内容.html> <输出.pdf> --margin "<对应值>" [--no-footer]
# 默认 --engine auto: Playwright 优先, 不可用时自动降级 WeasyPrint
```
满版模板(tech/warm)必须 `--margin "0 0 0 0" --no-footer`, 否则四周会留白、深色不出血。

## 环境依赖(首次)

```bash
pip install playwright && playwright install chromium   # 主引擎
pip install weasyprint                                   # 兜底(需系统库 pango/cairo)
```

## 自检清单(出 PDF 后必做, 不可跳过)

- [ ] 转图(`pdftoppm -png`)逐页肉眼看, **中文有无豆腐块/方框**
- [ ] **深色区(`.takeaway`/封面)里的文字是否可见**——深字压深底是最常见坑
- [ ] 表格、图表是否被分页**截断**
- [ ] 封面背景是否**出血到纸边**
- [ ] 数字列是否右对齐、对齐整齐

## 红线

- 深色背景区内的 `strong`/文字必须浅色(模板已处理; 自定义新区块时务必显式设白色)
- **数据类内容不可编造**; 演示/占位数据必须在脚注标注, 避免误导
- 不为了排版牺牲事实准确性

## 可视化选型(visual 模板)

读完原文**先判断数据性质再选图**(完整决策表见 `VISUAL-GUIDE.md`):
单指标→大数字 `.stat-hero` · 2–6 项对比→柱状图 · 时间趋势→折线图 · 占比→环形图 · 进度→`.bars` · 流程→`.steps` · 时间节点→`.timeline` · 多维→表格+`.pill` · 并列要点→`.grid`。
反例:别给 1–2 个数画柱状图(用大数字),别用柱状图表占比(用环形图)。
