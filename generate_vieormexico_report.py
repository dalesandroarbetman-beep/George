from __future__ import annotations

import html
import importlib.util
import json
from datetime import datetime
from itertools import combinations
from pathlib import Path


ROOT = Path(__file__).resolve().parent
TOOLS_PATH = ROOT / "tools" / "svsw_tools.py"
OUTPUT_DIR = ROOT / "output" / "vieormexico-2026-06-22"
HTML_PATH = OUTPUT_DIR / "短视频脚本提取与改写报告.html"
MD_PATH = OUTPUT_DIR / "短视频脚本提取与改写报告.md"
BRAND = "YOHO"
SITE_URL = "https://lnk.bio/YH-DIY-Jewelry"

VIDEO_NAME = (
    "@vieormexico-2026-06-22_2217-La-diferencia-entre-un-accesorio-y-una-"
    "pieza-que-destaca-está-en-la-calidad.-Acero-inoxidable-304L.-"
    "7654223806516448533 (1).mp4"
)
POST_CAPTION_ES = (
    "La diferencia entre un accesorio y una pieza que destaca está en la calidad. "
    "Acero inoxidable 304L."
)
ORIGINAL_ES = (
    "El error más común al comprar joyería es comprar mal desde el inicio. "
    "Muchas compran lo que les gusta. Lo que te gusta no siempre se vende, y ahí es donde pierdes dinero. "
    "Porque no es compra para ti; es comprar para tu propio negocio, y eso nadie te lo explica. "
    "Lo que sí funciona: piezas simples, fáciles de elegir. "
    "Así que ya sabes que es lo que te deja el doble. Y si quieres hacer tu pedido… "
    "www.vieormexico.com · República de Argentina 84."
)

TIMELINE = [
    ("00:00–00:05", "El error más común al comprar joyería es comprar mal desde el inicio.",
     "Hook：柜台全景切到讲述者，使用“常见错误”制造停留。"),
    ("00:06–00:12", "Muchas compran lo que les gusta. Lo que te gusta no siempre se vende, y ahí es donde pierdes dinero.",
     "痛点/冲突：用两款首饰与现金画面表达按个人喜好选货的风险。"),
    ("00:13–00:18", "Porque no es compra para ti; es comprar para tu propio negocio, y eso nadie te lo explica.",
     "反转：从“为自己买”切换到“为生意选货”。"),
    ("00:19–00:24", "Lo que sí funciona: piezas simples, fáciles de elegir.",
     "解决方案：展示简洁、容易选择的款式。"),
    ("00:25–00:28", "Así que ya sabes que es lo que te deja el doble.",
     "未经证实的双倍收益声明；YOHO 发布稿已删除。"),
    ("00:29–00:32", "Y si quieres hacer tu pedido…",
     "竞品 CTA：画面显示竞品网址与地址；YOHO 发布稿已替换为主页链接。"),
]


def load_tools():
    spec = importlib.util.spec_from_file_location("svsw_tools", TOOLS_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("无法加载 svsw_tools.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


TOOLS = load_tools()

# 本地规则库以中文为主，补上本次英文投放所需的高频风险词。
EN_PATCH = {
    "absolute_claims": [
        "best", "perfect", "never fades", "forever", "the only", "guaranteed",
        "miracle", "flawless", "absolutely", "#1", "top-rated",
    ],
    "cta_no_shop": [
        "Buy now", "Add to cart", "Tap to buy", "Shop now", "Get yours",
        "Order now", "Checkout", "Purchase", "Swipe up to buy",
    ],
    "health_efficacy": [
        "hypoallergenic", "medical grade", "heals", "cures", "therapeutic",
        "detox", "boosts immunity",
    ],
}
for rule in TOOLS.RULES:
    if rule["id"] in EN_PATCH:
        key = "banned_terms" if "banned_terms" in rule else "terms"
        rule[key] = list(rule.get(key, [])) + EN_PATCH[rule["id"]]


SCRIPTS = [
    {
        "id": "A",
        "name": "主拍稿",
        "angle": "日常百搭与选择效率",
        "platform": "TikTok / Reels / Shorts",
        "duration": "约 30–33 秒",
        "difference": "保留对标片的错误警示→选择困难→方法→CTA 节奏；把经营收益话术改成消费者可感知的穿搭选择。",
        "scene": "当前视频展示成品首饰，因此本稿自动聚焦成品首饰；零售与批发共用同一主页链接路径。",
        "hook": "One common jewelry mistake? Choosing the piece before thinking about the outfit.",
        "hook_zh": "一个很常见的首饰选择误区：还没想好怎么搭，就先挑了单品。",
        "body": (
            "A beautiful design can still stay in the box if it only works with one look. "
            "Start with clean shapes you can mix, layer, and wear again. "
            "Then add one bolder detail when you want more personality. "
            "At YOHO, you can explore finished jewelry across different styles."
        ),
        "body_zh": (
            "设计再好看，如果只能配一套造型，也可能一直放在首饰盒里。先从简洁轮廓开始，方便混搭、叠戴，也更容易重复使用。"
            "想增加个性时，再加一件更醒目的单品。YOHO 提供不同风格的成品首饰供你挑选。"
        ),
        "cta": "See the current styles and prices through the link in our bio.",
        "cta_zh": "通过主页链接查看当前款式和价格。",
        "hashtags": "#YOHOJewelry #EverydayJewelry #JewelryStyle #LinkInBio",
        "hooks": [
            ("Before you choose your next jewelry piece, ask one question: how will you style it?",
             "挑下一件首饰之前，先问自己一个问题：它准备怎么搭？"),
            ("A pretty jewelry piece is not useful if it never leaves the box.",
             "一件首饰再漂亮，如果从没戴出门，也发挥不了价值。"),
            ("If a piece only matches one outfit, you may not reach for it very often.",
             "如果一件首饰只能配一套衣服，你大概不会经常拿起它。"),
        ],
        "shots": [
            ("00:00–00:04", "保留对标片开场节奏：柜台全景，模特走近镜头。", "One common jewelry mistake?", "一个很常见的首饰选择误区？", "COMMON JEWELRY MISTAKE", "常见首饰误区"),
            ("00:04–00:08", "近景：模特左右手各拿一件首饰，停顿比较。", "Choosing the piece before thinking about the outfit.", "还没想好怎么搭，就先挑了单品。", "PIECE FIRST?", "先选单品？"),
            ("00:08–00:13", "用衣服或穿搭卡片替代原片现金画面；做撕纸/遮挡转场。", "A beautiful design can still stay in the box if it only works with one look.", "设计再好看，如果只能配一套造型，也可能一直放在首饰盒里。", "ONE LOOK ONLY", "只能搭一套"),
            ("00:13–00:18", "试戴简洁款，再叠加第二件；构图跟随原片，但替换具体动作。", "Start with clean shapes you can mix, layer, and wear again.", "先从简洁轮廓开始，方便混搭、叠戴，也更容易重复使用。", "MIX · LAYER · REWEAR", "混搭 · 叠戴 · 重复使用"),
            ("00:18–00:23", "展示首饰架，取下一件更醒目的单品。", "Then add one bolder detail when you want more personality.", "想增加个性时，再加一件更醒目的单品。", "ADD PERSONALITY", "增加个性"),
            ("00:23–00:28", "托盘与模特佩戴快切，保持原视频切镜密度。", "At YOHO, you can explore finished jewelry across different styles.", "YOHO 提供不同风格的成品首饰供你挑选。", "DIFFERENT STYLES AT YOHO", "YOHO 多种风格"),
            ("00:28–00:33", "模特指向主页链接位置；画面只出现 YOHO，不出现竞品信息。", "See the current styles and prices through the link in our bio.", "通过主页链接查看当前款式和价格。", "LINK IN BIO", "主页链接"),
        ],
    },
    {
        "id": "B",
        "name": "完整脚本 2",
        "angle": "一件首饰，三种穿搭",
        "platform": "Reels / TikTok",
        "duration": "约 27–31 秒",
        "difference": "从“别先买”改为现场搭配验证，用三个造型证明选择逻辑，正文不复用主稿表达。",
        "scene": "适合模特快速换上日常、叠穿、稍正式三套造型。",
        "hook": "Before choosing jewelry, try it with more than one outfit.",
        "hook_zh": "挑首饰之前，先试着配不止一套衣服。",
        "body": (
            "Start with a plain top. Add it to a layered look. Then try one dressier outfit. "
            "Clean shapes are easy to repeat, while one stronger detail can change the mood. "
            "YOHO gives you different finished styles to compare."
        ),
        "body_zh": (
            "先配一件基础上衣，再试试叠穿造型，最后换成稍正式的搭配。简洁轮廓更容易反复使用，"
            "而一个更醒目的细节就能改变整体感觉。你可以在 YOHO 比较不同成品款式。"
        ),
        "cta": "Browse YOHO from our profile link and check today's listed prices.",
        "cta_zh": "从主页链接进入 YOHO，查看今天页面显示的价格。",
        "hashtags": "#StyleItThreeWays #YOHOJewelry #OutfitIdeas #JewelryInspo",
        "shots": [
            ("00:00–00:05", "从托盘拿起一件主角首饰，镜头快速推近。", "Before choosing jewelry, try it with more than one outfit.", "挑首饰之前，先试着配不止一套衣服。", "TRY MORE THAN ONE LOOK", "多试几套穿搭"),
            ("00:05–00:13", "三次快切：基础上衣、叠穿、稍正式造型。", "Start with a plain top. Add it to a layered look. Then try one dressier outfit.", "先配基础上衣，再试叠穿，最后换成稍正式的造型。", "LOOK 1 · LOOK 2 · LOOK 3", "造型一 · 二 · 三"),
            ("00:13–00:20", "同一件简洁款反复入镜，再切到一件醒目款。", "Clean shapes are easy to repeat, while one stronger detail can change the mood.", "简洁轮廓容易重复使用，一个醒目细节就能改变整体感觉。", "SIMPLE OR BOLD", "简洁或醒目"),
            ("00:20–00:26", "平移拍摄 YOHO 成品首饰托盘。", "YOHO gives you different finished styles to compare.", "你可以在 YOHO 比较不同成品款式。", "COMPARE YOUR STYLE", "比较适合你的风格"),
            ("00:26–00:31", "模特指向个人主页链接位置。", "Browse YOHO from our profile link and check today's listed prices.", "从主页链接进入 YOHO，查看今天页面显示的价格。", "PROFILE LINK", "主页链接"),
        ],
    },
    {
        "id": "C",
        "name": "完整脚本 3",
        "angle": "先选感觉，再选款式",
        "platform": "Reels / Shorts",
        "duration": "约 26–30 秒",
        "difference": "把产品选择拆成 minimal / playful / bold 三种感觉，以分类决策代替主稿的百搭逻辑。",
        "scene": "适合一面首饰墙或三只托盘，通过手势和字幕做选择题。",
        "hook": "Too many jewelry options? Do not start with the product. Start with the mood.",
        "hook_zh": "首饰选择太多？别先盯着产品，先确定你想要的感觉。",
        "body": (
            "Choose one direction: minimal, playful, or bold. "
            "Now compare the shapes side by side and look for the style that fits your plan. "
            "A clear direction turns a crowded tray into a much simpler choice."
        ),
        "body_zh": (
            "先选一个方向：简约、俏皮，或醒目。再把轮廓并排比较，找到适合你计划的风格。"
            "方向清楚后，满满一托盘也会变得更容易选。"
        ),
        "cta": "Open our bio link to view the YOHO styles available now.",
        "cta_zh": "打开主页链接，查看 YOHO 当前可选的款式。",
        "hashtags": "#ChooseYourStyle #YOHO #JewelryGuide #CurrentStyles",
        "shots": [
            ("00:00–00:05", "面对首饰墙露出犹豫表情，手在多款之间移动。", "Too many jewelry options? Do not start with the product.", "首饰选择太多？别先盯着产品。", "TOO MANY OPTIONS?", "选择太多？"),
            ("00:05–00:09", "清空桌面，只留下三只托盘。", "Start with the mood.", "先确定你想要的感觉。", "CHOOSE THE MOOD", "先选感觉"),
            ("00:09–00:16", "依次指向三只托盘，字幕同步弹出。", "Choose one direction: minimal, playful, or bold.", "选一个方向：简约、俏皮，或醒目。", "MINIMAL · PLAYFUL · BOLD", "简约 · 俏皮 · 醒目"),
            ("00:16–00:24", "把三件首饰并排，再从拥挤托盘缩减为三件。", "Compare the shapes side by side. A clear direction makes the choice simpler.", "把轮廓并排比较。方向清楚，选择就更简单。", "COMPARE SIDE BY SIDE", "并排比较"),
            ("00:24–00:30", "举起最终选择，指向主页链接。", "Open our bio link to view the YOHO styles available now.", "打开主页链接，查看 YOHO 当前可选的款式。", "SEE YOHO STYLES", "查看 YOHO 款式"),
        ],
    },
    {
        "id": "D",
        "name": "完整脚本 4",
        "angle": "店铺备货：基础款加亮点款",
        "platform": "TikTok / Reels",
        "duration": "约 29–33 秒",
        "difference": "面向店主与批发采购场景，强调陈列组合和预算判断，不使用销量、利润或稀缺承诺。",
        "scene": "适合托盘配货、柜台陈列或店主真人讲解；仍使用与零售相同的主页链接。",
        "hook": "Buying jewelry for a shop? Personal taste should not make every decision.",
        "hook_zh": "为店铺采购首饰？别让个人喜好决定所有选择。",
        "body": (
            "Begin with simple shapes shoppers can understand at a glance. "
            "Use them as the base of the display, then add a few bolder designs for variety. "
            "Compare the current options and choose what fits your customers and your budget."
        ),
        "body_zh": (
            "先从顾客一眼就能看懂的简洁轮廓开始，把它们作为陈列基础，再加入少量更醒目的设计增加变化。"
            "比较当前选项，并根据你的顾客和预算做决定。"
        ),
        "cta": "Use the link on our profile to check YOHO's latest selection and listed prices.",
        "cta_zh": "通过主页链接查看 YOHO 最新上架选择和页面标价。",
        "hashtags": "#JewelryBusiness #RetailDisplay #YOHOJewelry #StockIdeas",
        "shots": [
            ("00:00–00:05", "柜台前直视镜头发问，保留原片真人讲述感。", "Buying jewelry for a shop? Personal taste should not make every decision.", "为店铺采购首饰？别让个人喜好决定所有选择。", "BUYING FOR A SHOP?", "为店铺采购？"),
            ("00:05–00:11", "手拿两款，把个人偏好款暂时放下。", "Begin with simple shapes shoppers can understand at a glance.", "先从顾客一眼就能看懂的简洁轮廓开始。", "START WITH SIMPLE SHAPES", "先选简洁轮廓"),
            ("00:11–00:18", "将简洁款排成陈列基础。", "Use them as the base of the display.", "把它们作为陈列的基础。", "BUILD THE BASE", "搭好基础"),
            ("00:18–00:24", "在基础款之间加入少量醒目款。", "Then add a few bolder designs for variety.", "再加入少量更醒目的设计增加变化。", "ADD VARIETY", "增加变化"),
            ("00:24–00:29", "托盘和站内款式列表快切，不显示虚构销售数据。", "Choose what fits your customers and your budget.", "根据你的顾客和预算做决定。", "CUSTOMERS + BUDGET", "顾客 + 预算"),
            ("00:29–00:33", "模特指向主页链接位置。", "Use the link on our profile to check YOHO's latest selection and listed prices.", "通过主页链接查看 YOHO 最新上架选择和页面标价。", "VIEW YOHO", "查看 YOHO"),
        ],
    },
]


def publish_text(item):
    """Only the English text that could actually be published."""
    return "\n".join([item["hook"], item["body"], item["cta"], item["hashtags"]])


original_checks = {
    item["id"]: TOOLS.ngram_check(publish_text(item), ORIGINAL_ES, n=5)
    for item in SCRIPTS
}
pair_checks = []
for left, right in combinations(SCRIPTS, 2):
    result = TOOLS.ngram_check(publish_text(left), publish_text(right), n=5)
    pair_checks.append({
        "pair": f"{left['id']} ↔ {right['id']}",
        "verdict": result["verdict"],
        "max_consecutive": result["max_consecutive"],
        "segments": result["segments"],
    })

compliance_rows = []
for item in SCRIPTS:
    result = TOOLS.compliance_check(
        publish_text(item), has_shop_cart=False, whitelist=[], audit_aware=True
    )
    compliance_rows.append({"label": f"脚本 {item['id']}", **result})

assert all(result["verdict"] == "PASS" for result in original_checks.values()), original_checks
assert all(row["verdict"] == "PASS" for row in pair_checks), pair_checks
assert all(row["BLOCK"] == 0 for row in compliance_rows), compliance_rows

# 品牌隔离：竞品事实只能留在对标审计区，不能进入任何 YOHO 发布正文。
for item in SCRIPTS:
    published = publish_text(item).lower()
    assert "vieor" not in published and "304l" not in published
    assert "república de argentina" not in published and "double" not in published


def esc(value):
    return html.escape(str(value), quote=True)


def bilingual(label, en, zh):
    return (
        f'<div class="label">{esc(label)}</div>'
        f'<div class="en-line">{esc(en)}</div>'
        f'<div class="zh-ref">中文参考翻译：{esc(zh)}</div>'
    )


def publish_html(item):
    return (
        '<div class="publish"><h4>纯英文发布版</h4>'
        + bilingual("Hook", item["hook"], item["hook_zh"])
        + bilingual("Body", item["body"], item["body_zh"])
        + bilingual("CTA", item["cta"], item["cta_zh"])
        + f'<div class="label">Hashtag</div><div class="en-line">{esc(item["hashtags"])}</div>'
        + '<p class="internal">复制发布时仅复制英文；中文参考翻译禁止进入英文视频成片。</p></div>'
    )


def storyboard_html(item):
    rows = "".join(
        f"<tr><td class='time'>{esc(t)}</td><td>{esc(action)}</td>"
        f"<td><div class='en-cell'>{esc(vo)}</div><div class='zh-mini'>中文参考：{esc(vo_zh)}</div></td>"
        f"<td><div class='en-cell'>{esc(overlay)}</div><div class='zh-mini'>中文参考：{esc(overlay_zh)}</div></td></tr>"
        for t, action, vo, vo_zh, overlay, overlay_zh in item["shots"]
    )
    return (
        '<h4>拍摄分镜版</h4><div class="table-wrap"><table><thead><tr>'
        '<th>时间</th><th>动作 / 画面</th><th>英文口播</th><th>英文屏幕字幕</th>'
        f'</tr></thead><tbody>{rows}</tbody></table></div>'
    )


def script_html(item, main=False):
    badge = '<span class="tag tag-main">优先拍摄</span>' if main else f'<span class="tag">脚本 {esc(item["id"])}</span>'
    return (
        f'<article class="script-card"><h3>{badge} {esc(item["name"])} · {esc(item["angle"])}</h3>'
        f'<p class="meta">适用平台：{esc(item["platform"])} · 参考时长：{esc(item["duration"])}</p>'
        f'<p><strong>差异点：</strong>{esc(item["difference"])}</p>'
        f'<p><strong>适用场景：</strong>{esc(item["scene"])}</p>'
        + storyboard_html(item) + publish_html(item) + '</article>'
    )


main = SCRIPTS[0]
backup_hooks_html = "".join(
    f'<div class="hook-card"><div class="en-line">{esc(en)}</div>'
    f'<div class="zh-ref">中文参考翻译：{esc(zh)}</div></div>'
    for en, zh in main["hooks"]
)
timeline_html = "".join(
    f'<tr><td class="time">{esc(t)}</td><td class="original">{esc(caption)}</td><td>{esc(note)}</td></tr>'
    for t, caption, note in TIMELINE
)
pair_html = "".join(
    f'<tr><td>{esc(row["pair"])}</td><td>{row["max_consecutive"]} 词</td>'
    f'<td><span class="tag tag-pass">{esc(row["verdict"])}</span></td></tr>'
    for row in pair_checks
)
original_ngram_html = "".join(
    f'<tr><td>脚本 {esc(item["id"])}</td><td>{original_checks[item["id"]]["max_consecutive"]} 词</td>'
    f'<td><span class="tag tag-pass">{esc(original_checks[item["id"]]["verdict"])}</span></td></tr>'
    for item in SCRIPTS
)
compliance_html = "".join(
    f'<tr><td>{esc(row["label"])}</td><td>{row["BLOCK"]}</td><td>{row["WARN"]}</td>'
    f'<td>{row["NOTE"]}</td><td><span class="tag tag-pass">{esc(row["gate"])}</span></td>'
    f'<td>{"未命中风险项" if not row["findings"] else esc(json.dumps(row["findings"], ensure_ascii=False))}</td></tr>'
    for row in compliance_rows
)

generated_at = datetime.now().strftime("%Y-%m-%d %H:%M")

html_report = f"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>YOHO 短视频脚本提取与改写报告</title>
<style>
:root{{--bg:#0d1117;--panel:#161b22;--border:#30363d;--text:#c9d1d9;--muted:#8b949e;--accent:#58a6ff;--warn:#f0883e;--block:#f85149;--ok:#3fb950}}
*{{box-sizing:border-box}} body{{margin:0;background:var(--bg);color:var(--text);font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif;line-height:1.65}}
.container{{max-width:1120px;margin:auto;padding:28px}} h1,h2,h3,h4{{color:#f0f6fc}} h1{{font-size:28px;border-bottom:1px solid var(--border);padding-bottom:12px}} h2{{margin-top:40px}} h4{{margin-bottom:8px}}
.meta,.internal{{color:var(--muted);font-size:14px}} .section,.script-card,.publish{{background:var(--panel);border:1px solid var(--border);border-radius:9px;padding:20px;margin:16px 0}}
.script-card{{background:#111820}} .publish{{background:#0f151d}} .notice{{border-left:4px solid var(--warn);background:rgba(240,136,62,.08);padding:12px 14px;margin:14px 0}}
.summary{{display:grid;grid-template-columns:repeat(4,1fr);gap:10px}} .summary div{{background:var(--panel);border:1px solid var(--border);border-radius:8px;padding:12px}} .summary b{{display:block;color:#f0f6fc}}
.table-wrap{{overflow-x:auto}} table{{width:100%;border-collapse:collapse;margin:10px 0}} th,td{{text-align:left;vertical-align:top;padding:10px 11px;border-bottom:1px solid var(--border)}} th{{color:var(--muted);white-space:nowrap}}
.time{{white-space:nowrap;color:var(--muted);font-family:ui-monospace,monospace}} .original{{font-style:italic;color:#aab3bd}} .label{{color:var(--accent);font-size:12px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;margin-top:12px}}
.en-line,.en-cell{{color:#f0f6fc}} .zh-ref,.zh-mini{{border-left:3px solid rgba(88,166,255,.55);padding-left:11px;color:var(--muted);font-size:14px;margin:4px 0 12px}} .zh-mini{{margin-top:6px}}
.tag{{display:inline-block;padding:2px 8px;border-radius:999px;background:rgba(88,166,255,.14);color:var(--accent);font-size:12px}} .tag-main{{background:rgba(240,136,62,.14);color:var(--warn)}} .tag-pass{{background:rgba(63,185,80,.14);color:var(--ok)}}
.hook-grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}} .hook-card{{background:#0f151d;border:1px solid var(--border);border-radius:8px;padding:12px}} a{{color:var(--accent)}} details{{margin:12px 0}} .footer{{border-top:1px solid var(--border);margin-top:42px;padding-top:20px;color:var(--muted);font-size:13px}}
@media(max-width:760px){{.container{{padding:16px}}.summary,.hook-grid{{grid-template-columns:1fr}}.section,.script-card{{padding:14px}}}}
</style></head><body><main class="container">
<h1>YOHO 短视频脚本提取与改写报告</h1>
<p class="meta">生成时间：{esc(generated_at)} · 对标素材时长：00:32 · 投放语言：英文 · 发布路径：主页链接 → 独立站</p>
<div class="summary"><div><span>品牌</span><b>YOHO</b></div><div><span>当前产品线</span><b>成品首饰</b></div><div><span>交付</span><b>4 套完整脚本</b></div><div><span>门禁</span><b style="color:var(--ok)">BLOCK 0</b></div></div>
<p>独立站：<a href="{esc(SITE_URL)}">{esc(SITE_URL)}</a></p>

<section class="section"><h2>一、主拍执行区</h2>
<div class="notice"><strong>执行原则：</strong>模特可跟随对标视频的时长、讲述节奏和镜头密度；动作、构图、产品与文案改为 YOHO 版本。当前素材展示成品首饰，因此本次自动选择成品首饰线。</div>
{script_html(main, main=True)}
<h3>备用 Hook（任选一个替换主稿开场）</h3><div class="hook-grid">{backup_hooks_html}</div>
</section>

<section class="section"><h2>二、对标视频拆解</h2>
<div class="notice"><strong>识读说明：</strong>已在本机逐段查看 MP4 的西语烧录字幕，没有调用外部 API。未做音频转写，字幕与实际口播是否逐字一致仍应在拍摄前对原音复核。</div>
<div class="table-wrap"><table><thead><tr><th>时间</th><th>画面 / 字幕原文</th><th>备注</th></tr></thead><tbody>{timeline_html}</tbody></table></div>
<p><strong>结构：</strong>Hook（常见错误）→ 痛点（个人喜好不等于顾客选择）→ 反转（为生意选货）→ 方法（简洁易选）→ CTA。</p>
<p><strong>钩子类型：</strong>错误警示型 + 损失规避型。</p>
<details><summary>对照原文（西语烧录字幕合并）</summary><p class="original">{esc(ORIGINAL_ES)}</p></details>
<details><summary>原发布文案（来自文件名）</summary><p class="original">{esc(POST_CAPTION_ES)}</p></details>
<div class="notice"><strong>品牌与合规隔离：</strong>VIE OR Mexico、竞品网址、竞品地址、304L 材质和“获得双倍收益”只保留在本审计区。YOHO 未确认材质，也未提供数字声明白名单，因此这些信息全部未进入发布稿。</div>
</section>

<section class="section"><h2>三、其他完整脚本</h2>
<p class="meta">三套脚本分别改写选择机制、叙事角度和拍摄动作，避免只换 Hook、正文雷同。</p>
{''.join(script_html(item) for item in SCRIPTS[1:])}
</section>

<section class="section"><h2>四、防雷同与合规门禁</h2>
<h3>与原片的 5-gram 校验</h3><p class="meta">只比较实际英文发布正文与西语原文；结构、表头、中文翻译和分镜字段未参与。</p>
<div class="table-wrap"><table><thead><tr><th>稿件</th><th>最大连续重复</th><th>结果</th></tr></thead><tbody>{original_ngram_html}</tbody></table></div>
<h3>四套脚本互检</h3><div class="table-wrap"><table><thead><tr><th>组合</th><th>最大连续重复</th><th>结果</th></tr></thead><tbody>{pair_html}</tbody></table></div>
<h3>合规自检</h3><p><span class="tag tag-pass">BLOCK 已清零</span> 无小黄车 · 白名单为空 · 仅扫描实际英文发布正文。</p>
<div class="table-wrap"><table><thead><tr><th>稿件</th><th>BLOCK</th><th>WARN</th><th>NOTE</th><th>门禁</th><th>结果</th></tr></thead><tbody>{compliance_html}</tbody></table></div>
<div class="notice"><strong>已处理：</strong>删除竞品双倍收益、304L、网址、地址与品牌；未添加销量、评分、保修、稀缺库存、功效或绝对化用语。</div>
</section>

<section class="section"><h2>五、使用说明</h2><ol>
<li>优先拍脚本 A；需要测试开场时，只替换备用 Hook，其余镜头可保持。</li>
<li>脚本 B、C、D 是不同角度的完整备选，不是主稿的换词版。</li>
<li>模特参考对标片的时长和镜头密度，但不要复刻竞品标识、地址、网页或原句。</li>
<li>发布时只复制英文 Hook、Body、CTA 和 Hashtag；中文翻译只用于内部审稿。</li>
<li>产品线跟随上传视频自动判断。本片为成品首饰；若下次画面是 DIY 配件，则切换到 DIY 材料线。</li>
<li>CTA 固定走主页链接。没有小黄车时，不使用 Buy now、Add to cart、Tap to buy。</li>
<li>任何材质、价格优惠、销量、评价或承诺，只有得到可核实信息后才能加入。</li>
</ol></section>
<div class="footer">Generated locally · Built-in Computer Use inspection · No external API used.</div>
</main></body></html>"""


def md_bilingual(label, en, zh):
    return f"**{label} (EN)**  \n{en}\n\n> 中文参考翻译：{zh}\n"


def md_publish(item):
    return (
        "#### 纯英文发布版\n\n"
        + md_bilingual("Hook", item["hook"], item["hook_zh"]) + "\n"
        + md_bilingual("Body", item["body"], item["body_zh"]) + "\n"
        + md_bilingual("CTA", item["cta"], item["cta_zh"]) + "\n"
        + f"**Hashtag (EN)**  \n{item['hashtags']}\n\n"
        + "> 复制发布时仅复制英文；中文参考翻译禁止进入英文视频成片。\n"
    )


def md_storyboard(item):
    rows = []
    for t, action, vo, vo_zh, overlay, overlay_zh in item["shots"]:
        rows.append(
            f"| {t} | {action} | {vo}<br>中文参考：{vo_zh} | {overlay}<br>中文参考：{overlay_zh} |"
        )
    return (
        "#### 拍摄分镜版\n\n| 时间 | 动作 / 画面 | 英文口播 | 英文屏幕字幕 |\n"
        "|---|---|---|---|\n" + "\n".join(rows) + "\n"
    )


def md_script(item, main=False):
    lead = "优先拍摄 · " if main else ""
    return f"""### {lead}{item['name']} · {item['angle']}

- 适用平台：{item['platform']}
- 参考时长：{item['duration']}
- 差异点：{item['difference']}
- 适用场景：{item['scene']}

{md_storyboard(item)}

{md_publish(item)}
"""


timeline_md = "\n".join(f"| {t} | *{caption}* | {note} |" for t, caption, note in TIMELINE)
hooks_md = "\n\n".join(
    f"{idx}. **EN:** {en}\n\n   > 中文参考翻译：{zh}"
    for idx, (en, zh) in enumerate(main["hooks"], 1)
)
original_check_md = "\n".join(
    f"| 脚本 {item['id']} | {original_checks[item['id']]['max_consecutive']} 词 | {original_checks[item['id']]['verdict']} |"
    for item in SCRIPTS
)
pair_md = "\n".join(
    f"| {row['pair']} | {row['max_consecutive']} 词 | {row['verdict']} |" for row in pair_checks
)
compliance_md = "\n".join(
    f"| {row['label']} | {row['BLOCK']} | {row['WARN']} | {row['NOTE']} | {row['gate']} |"
    for row in compliance_rows
)

markdown_report = f"""# YOHO 短视频脚本提取与改写报告

生成时间：{generated_at}  
对标素材时长：`00:32` · 投放语言：英文 · 发布路径：主页链接 → 独立站  
品牌：**YOHO** · 当前产品线：**成品首饰** · 独立站：[打开链接]({SITE_URL})

## 一、主拍执行区

> **执行原则：**模特可跟随对标视频的时长、讲述节奏和镜头密度；动作、构图、产品与文案改为 YOHO 版本。当前素材展示成品首饰，因此本次自动选择成品首饰线。

{md_script(main, main=True)}

### 备用 Hook（任选一个替换主稿开场）

{hooks_md}

## 二、对标视频拆解

> **识读说明：**已在本机逐段查看 MP4 的西语烧录字幕，没有调用外部 API。未做音频转写，字幕与实际口播是否逐字一致仍应在拍摄前对原音复核。

| 时间 | 画面 / 字幕原文 | 备注 |
|---|---|---|
{timeline_md}

**结构：**Hook（常见错误）→ 痛点（个人喜好不等于顾客选择）→ 反转（为生意选货）→ 方法（简洁易选）→ CTA。

**钩子类型：**错误警示型 + 损失规避型。

<details><summary>对照原文（西语烧录字幕合并）</summary>

*{ORIGINAL_ES}*

</details>

<details><summary>原发布文案（来自文件名）</summary>

*{POST_CAPTION_ES}*

</details>

> **品牌与合规隔离：**VIE OR Mexico、竞品网址、竞品地址、304L 材质和“获得双倍收益”只保留在本审计区。YOHO 未确认材质，也未提供数字声明白名单，因此这些信息全部未进入发布稿。

## 三、其他完整脚本

三套脚本分别改写选择机制、叙事角度和拍摄动作，避免只换 Hook、正文雷同。

{''.join(md_script(item) for item in SCRIPTS[1:])}

## 四、防雷同与合规门禁

### 与原片的 5-gram 校验

只比较实际英文发布正文与西语原文；结构、表头、中文翻译和分镜字段未参与。

| 稿件 | 最大连续重复 | 结果 |
|---|---:|---|
{original_check_md}

### 四套脚本互检

| 组合 | 最大连续重复 | 结果 |
|---|---:|---|
{pair_md}

### 合规自检

无小黄车 · 白名单为空 · 仅扫描实际英文发布正文。

| 稿件 | BLOCK | WARN | NOTE | 门禁 |
|---|---:|---:|---:|---|
{compliance_md}

> **已处理：**删除竞品双倍收益、304L、网址、地址与品牌；未添加销量、评分、保修、稀缺库存、功效或绝对化用语。

## 五、使用说明

1. 优先拍脚本 A；需要测试开场时，只替换备用 Hook，其余镜头可保持。
2. 脚本 B、C、D 是不同角度的完整备选，不是主稿的换词版。
3. 模特参考对标片的时长和镜头密度，但不要复刻竞品标识、地址、网页或原句。
4. 发布时只复制英文 Hook、Body、CTA 和 Hashtag；中文翻译只用于内部审稿。
5. 产品线跟随上传视频自动判断。本片为成品首饰；若下次画面是 DIY 配件，则切换到 DIY 材料线。
6. CTA 固定走主页链接。没有小黄车时，不使用 Buy now、Add to cart、Tap to buy。
7. 任何材质、价格优惠、销量、评价或承诺，只有得到可核实信息后才能加入。
"""

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
HTML_PATH.write_text(html_report, encoding="utf-8")
MD_PATH.write_text(markdown_report, encoding="utf-8")

summary = {
    "html": str(HTML_PATH),
    "markdown": str(MD_PATH),
    "scripts": len(SCRIPTS),
    "backup_hooks": len(main["hooks"]),
    "original_ngram": original_checks,
    "pairwise_max": max(row["max_consecutive"] for row in pair_checks),
    "pairwise": pair_checks,
    "compliance": [
        {k: row[k] for k in ("label", "BLOCK", "WARN", "NOTE", "gate")}
        for row in compliance_rows
    ],
}
print(json.dumps(summary, ensure_ascii=True, indent=2))
