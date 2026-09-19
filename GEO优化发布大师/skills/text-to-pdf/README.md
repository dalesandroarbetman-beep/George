# text-to-pdf

把文字变成专业、美观 PDF 的 agent skill。Agent 把内容组织成结构化 HTML,套用现成模板,即可产出 5 种风格、中文字体内嵌、跨环境渲染一致的高质量 PDF。

> 核心理念:**决定美观的是模板 CSS,不是转换工具**。Agent 只负责填内容,样式与字体由 skill 兜底。

---

## 一、能力概述(内容)

- **5 种风格模板**:咨询报告 / 杂志长文 / 科技暗色 / 暖色招生 / 超级可视化
- **中文字体内嵌**:思源黑体+宋体(各 Regular/Bold)子集打包,**不依赖目标环境是否装中文字体**
- **稳定分页**:标题不孤行、组件不截断、孤寡行控制——万字长文格式不乱
- **可视化组件库**(visual 模板):KPI 卡、大统计、对比表、进度条、时间线、流程步骤、柱/折线图、四色高亮框、要点网格、结论框
- **双引擎**:Playwright(Chromium,主)+ WeasyPrint(兜底),Chromium 不可用时自动降级

---

## 二、五种风格(选型)

| 风格 | 气质 | 适用 | 转换 margin / footer |
|---|---|---|---|
| `report` 咨询蓝 | 沉稳专业 | 商业/分析报告、复盘 | `--margin "20mm 17mm 18mm 17mm"`(默认,带页脚页码) |
| `editorial` 杂志红 | 编辑长文、首字下沉 | 深度文章、观点、方法论 | `--margin "22mm 24mm 22mm 24mm"` |
| `tech` 科技青 | 现代暗色 | AI 产品、技术白皮书、数据报告 | `--margin "0 0 0 0" --no-footer`(满版深色) |
| `warm` 暖橙 | 亲和活力 | 培训招生、活动一页纸 | `--margin "0 0 0 0" --no-footer`(满版浅色) |
| `visual` 可视化旗舰 | 强可视化+长文 | 万字报告、多章节、数据密集 | `--margin "20mm 17mm 18mm 17mm"`(默认,带页脚页码) |

`visual` 是 `report` 的超集升级版:多了目录、自动章节编号、完整可视化组件库与长文分页保障。

---

## 三、目录结构(架构)

```
text-to-pdf/
├── SKILL.md              # 给 agent 的触发与流程说明
├── README.md             # 本文件
├── scripts/
│   └── html2pdf.py       # 转换核心:HTML → PDF(Playwright 主 + WeasyPrint 兜底)
├── templates/
│   ├── fonts.css         # 字体挂载(@font-face,被各模板 @import)
│   ├── report.css/.html  # 咨询报告
│   ├── editorial.css/.html
│   ├── tech.css/.html
│   ├── warm.css/.html
│   └── visual.css/.html  # 超级可视化(组件库 + 长文骨架)
├── fonts/                # 内嵌中文字体(woff2,子集 ~23MB)
│   ├── SourceHanSansSC-Regular.woff2
│   ├── SourceHanSansSC-Bold.woff2
│   ├── SourceHanSerifSC-Regular.woff2
│   └── SourceHanSerifSC-Bold.woff2
└── examples/             # 5 个风格的样张 PDF
```

---

## 四、工作流程(框架)

```
文字  →  ① 判型+结构化  →  ② 套模板生成 HTML  →  ③ 样式自动(含内嵌字体)  →  ④ 转 PDF + 自检
```

1. **判型+结构化**:读输入,判断文档类型,拆成标题/段落/表格/要点/数据/图表等语义块
2. **套模板生成 HTML**:复制对应模板 `<head>`(含 `<link rel="stylesheet" href="<风格>.css">`),内容填进 `<body>`。**HTML 必须与模板 CSS 同目录**
3. **样式自动**:模板 CSS 已 `@import "fonts.css"`,字体自动生效,不需手写 CSS
4. **转 PDF + 自检**:调 `html2pdf.py`,然后转图肉眼检查(见 SKILL.md 自检清单)

---

## 五、安装(依赖)

> Python 3.8+。中文字体已内嵌,无需在目标机安装中文字体。

```bash
# 主引擎(推荐,美观上限最高)
pip install playwright
playwright install chromium

# 兜底引擎(可选,但建议装上以防 Chromium 不可用)
pip install weasyprint
# WeasyPrint 需系统库:
#   Ubuntu/Debian: apt-get install libpango-1.0-0 libpangocairo-1.0-0 libcairo2 libgdk-pixbuf-2.0-0
#   macOS:         brew install pango

# 可选:校验 PDF 页数
pip install pypdf
```

---

## 六、使用

```bash
# 通用形式(margin 按风格表填; tech/warm 加 --no-footer)
python3 scripts/html2pdf.py <内容.html> <输出.pdf> --margin "<对应值>" [--no-footer]

# 示例
python3 scripts/html2pdf.py my_report.html out.pdf                          # report/visual(默认)
python3 scripts/html2pdf.py my_slide.html  out.pdf --margin "0 0 0 0" --no-footer   # tech/warm 满版
```

参数:
- `--engine auto|playwright|weasyprint`(默认 auto:Playwright 优先,失败自动降级)
- `--margin "上 右 下 左"`,支持 1-4 值(同 CSS 简写);满版用 `"0 0 0 0"`
- `--no-footer`:不显示页脚页码(满版/暗色模板用)

---

## 七、字体说明

- 内嵌字体子集自 Noto/思源(同源),范围:**CJK 基本区(U+4E00–9FFF)+ 标点 + 箭头/带圈数字/几何符号 + 拉丁**,覆盖现代中文约 99.9%
- 字体族名为 `Source Han Sans SC` / `Source Han Serif SC`,各模板字体栈已以其打头、系统字体在后兜底
- **跨环境一致性**:只要 `fonts/` 目录随包,任何机器渲染结果一致,不依赖系统中文字体

---

## 八、已知问题与限制(问题)

1. **目录无精确页码**:Chromium 路线不支持 CSS 自动页码,`visual` 目录为章节锚点(无页码数字)。需精确页码须走 WeasyPrint,但会牺牲部分 flex 可视化效果。
2. **极生僻字回退**:超出子集的异体字/扩展区汉字会回退系统字体;若目标机无中文字体,这些字可能缺失。报告/文章场景基本不触发。
3. **WeasyPrint 降级差异**:Chromium 不可用时自动降级 WeasyPrint,但 flex 布局(visual 的流程/网格、tech 的数据卡)在 WeasyPrint 下可能堆叠错位。**强烈建议装 Chromium 走 Playwright**。
4. **满版模板参数**:`tech`/`warm` 必须 `--margin "0 0 0 0" --no-footer`,否则四周留白、深色不出血。
5. **SVG 图表为静态手写**:模板内图表是手写 SVG 示例,非数据驱动。需按真实数据出图时,agent 自行生成 SVG 填入 `.chart` 容器。
6. **首次较慢**:`playwright install chromium` 需下载约 150MB;之后复用。

---

## 九、给 AI Agent 的集成提示

1. 把整个 `text-to-pdf/` 目录放到 agent 的 skill 目录(如 `/mnt/skills/user/`)
2. Agent 读 `SKILL.md` 获取触发条件与流程
3. 仿写内容时,直接读 `templates/<风格>.html` 学结构与 class 命名
4. 转换命令的 `--margin` / `--no-footer` 按上方风格表对应填写
5. 出 PDF 后务必转图自检(尤其:深色区文字是否可见、组件是否跨页截断、中文有无缺字)

---

## 十、两个版本怎么选

| 版本 | 体积 | 适用 |
|---|---|---|
| **完整版** `text-to-pdf.zip`(含字体) | ~21MB | 目标环境可能没中文字体,或要求渲染绝对一致 |
| **轻量版** `text-to-pdf-lite.zip`(无字体) | ~50KB | skill 平台有体积限制;目标环境已有中文字体(Mac/Win/多数 Linux) |

轻量版去掉了 `fonts/`、`fonts.css` 留空壳。各模板字体栈含系统 fallback(苹方/思源/Noto/雅黑),效果与完整版几乎一致——**美观靠 CSS,不靠字体内嵌**。仅当目标环境完全无中文字体时,轻量版才会缺字。

## 十一、可视化选型

`VISUAL-GUIDE.md` 提供"数据特征 → 最优图表"决策表 + 环形图等 SVG 模板。Agent 读完原文应据此选图(单指标→大数字、对比→柱状、趋势→折线、占比→环形、进度→进度条…),而非一律堆文字或乱用图表。

## 十二、本轮优化
- **字号 +1pt**(10.5→11.5pt 等),阅读更舒适;大标题不变,布局稳定
- **字体加载加固**:生成 PDF 前等 `document.fonts.ready`,根治偶发缺字/白页(此前 woff2 未加载完就出 PDF 会丢字)
- margin 参数支持 1–4 值(对齐 CSS 简写)
- 新增可视化选型指南 + 环形图模板
