#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
svsw_tools.py — 短视频脚本工作流 · GPT / Code Interpreter 版校验工具

从 WorkBuddy skill `short-video-script-workflow` 移植而来，合并了原 skill 的两个脚本：
  - scripts/ngram_check.py      -> ngram_check()
  - scripts/compliance_check.py -> compliance_check()

与本地版的差异（为适配 ChatGPT Code Interpreter 沙箱而改）：
  1. 只用 Python 标准库（re / json）。沙箱里 pip install 与联网均不可用，
     因此去掉 pyyaml、yt-dlp、ffmpeg 相关的一切依赖。
  2. 输入改为「字符串」而非「文件路径」。沙箱没有原 skill 目录，读文件必然失败。
  3. 去掉 argparse / sys.exit 的 CLI 外壳，改为纯函数调用。
  4. 合规规则内置在 RULES 常量里，不再做 YAML 自动发现（沙箱无从发现）。
     需要扩展时直接改 RULES，或调用时传入 custom_rules。
  5. YAML 规则加载整体移除 —— Code Interpreter 装不了 pyyaml。
     如果本地已有行业专用 YAML，请把规则人工翻译成 RULES 条目后贴进来。

用法（在 ChatGPT 的 Code Interpreter 里）：

    exec(open('/mnt/data/svsw_tools.py').read())

    r = ngram_check(new_script_text, original_script_text, n=5)
    print(r['verdict'], r['max_consecutive'])

    c = compliance_check(english_script_text, has_shop_cart=False)
    print(c['BLOCK'], c['WARN'], c['NOTE'])
    print(format_compliance(c))
"""

import json
import re

__all__ = [
    'ngram_check', 'compliance_check',
    'format_ngram', 'format_compliance',
    'RULES', 'UNVERIFIED_PATTERNS',
]

# ==================================================================
# 一、n-gram 防雷同客观校验
# ==================================================================

CJK_RE = re.compile(r'[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]')
WORD_RE = re.compile(r"[0-9a-z\u00e0-\u00ff\u00c0-\u00dd]+")
LATIN_CHAR_RE = re.compile(r'[a-zA-Z0-9]')


def _detect_script(text):
    """判断文本书写系统（按 token 数）：cjk / latin / mixed / unknown"""
    if not text:
        return 'unknown'
    cjk = len(CJK_RE.findall(text))
    latin = len(WORD_RE.findall(text.lower()))
    total = cjk + latin
    if total == 0:
        return 'unknown'
    r = cjk / total
    if r > 0.7:
        return 'cjk'
    if r < 0.1:
        return 'latin'
    return 'mixed'


def _dominant_script(text):
    """
    按「字符数」判断主导书写系统。
    中文标题按字 token 化后会被放大，字符比例更能反映真实正文语言。
    """
    if not text:
        return 'unknown'
    cjk = len(CJK_RE.findall(text))
    latin = len(LATIN_CHAR_RE.findall(text))
    total = cjk + latin
    if total == 0:
        return 'unknown'
    if cjk / total > 0.55:
        return 'cjk'
    if latin / total > 0.55:
        return 'latin'
    return 'mixed'


def _strip_markdown(text):
    """剥离 Markdown 噪声：代码块、时间轴、表格管道、标题与强调符号。"""
    text = re.sub(r'```.*?```', ' ', text, flags=re.S)
    text = re.sub(r'`[^`]*`', ' ', text)
    text = re.sub(r'\d+\s*[-\u2013\u2014~]\s*\d+(\.\d+)?\s*s?\b', ' ', text)
    text = re.sub(r'\b\d+(\.\d+)?s\b', ' ', text)
    text = re.sub(r'^\s*\|?[\s:\-\|]+\|[\s:\-\|]*$', ' ', text, flags=re.M)
    text = text.replace('|', ' ')
    text = re.sub(r'^\s*[#>\-\*\+]\s*', ' ', text, flags=re.M)
    text = re.sub(r'\*\*|\*|__|~~', ' ', text)
    return text


def _tokenize(text):
    """分词：CJK 逐字，拉丁按词，统一小写后比较。"""
    text = text.lower()
    text = re.sub(r'[^\w\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff\u00e0-\u00ff]+', ' ', text)
    tokens = []
    for seg in text.split():
        lat = ''
        for ch in seg:
            if CJK_RE.match(ch):
                if lat:
                    tokens.append(lat)
                    lat = ''
                tokens.append(ch)
            elif ch.isalnum() or ch.isdigit():
                lat += ch
            else:
                if lat:
                    tokens.append(lat)
                    lat = ''
        if lat:
            tokens.append(lat)
    return tokens


def _ngram_set(tokens, n):
    if len(tokens) < n:
        return set()
    return {tuple(tokens[i:i + n]) for i in range(len(tokens) - n + 1)}


def _longest_repeat(a, b, n):
    """返回 (最大连续重复词数, 重复片段列表)"""
    bg = _ngram_set(b, n)
    if not bg or len(a) < n:
        return 0, []

    covered = [tuple(a[i:i + n]) in bg for i in range(len(a) - n + 1)]
    segments = []
    i = 0
    while i < len(covered):
        if covered[i]:
            j = i
            while j + 1 < len(covered) and covered[j + 1]:
                j += 1
            run_len = (j - i + 1) + (n - 1)
            segments.append({
                'start': i,
                'length': run_len,
                'text': ' '.join(a[i:i + run_len]),
            })
            i = j + 1
        else:
            i += 1

    best = max((s['length'] for s in segments), default=0)
    segments.sort(key=lambda s: -s['length'])
    return best, segments


def ngram_check(new_text, original_text, n=5, strip_markdown=True):
    """
    n-gram 防雷同客观校验。

    参数
        new_text       : 新稿（待校验的改写稿/变体）
        original_text  : 原稿 / 对标稿
        n              : n-gram 的 N，默认 5（最大连续重复 < 5 词为 PASS）
        strip_markdown : 是否先剥离 Markdown 噪声，默认 True

    返回 dict，关键键：
        verdict         : 'PASS' / 'FAIL' / 'SKIP'
        max_consecutive : 最大连续重复词数
        segments        : 重复片段（按长度降序，最多 10 条）
        cross_language_skip : 是否因跨语种而跳过词面比对
    """
    if strip_markdown:
        new_text = _strip_markdown(new_text)
        original_text = _strip_markdown(original_text)

    sa, sb = _detect_script(new_text), _detect_script(original_text)
    da, db = _dominant_script(new_text), _dominant_script(original_text)
    a_tok, b_tok = _tokenize(new_text), _tokenize(original_text)

    cross_lang = da in ('cjk', 'latin') and db in ('cjk', 'latin') and da != db

    result = {
        'n': n,
        'script_new': sa,
        'script_original': sb,
        'dominant_script_new': da,
        'dominant_script_original': db,
        'tokens_new': len(a_tok),
        'tokens_original': len(b_tok),
        'cross_language_skip': cross_lang,
    }

    if cross_lang:
        result.update({
            'max_consecutive': 0,
            'verdict': 'SKIP',
            'reason': (f'跨语种主导文案（{da} vs {db}），词面 n-gram 不适用，'
                       f'需改用角度/结构/卖点表述的定性比对'),
            'segments': [],
        })
        return result

    mx, segs = _longest_repeat(a_tok, b_tok, n)
    result.update({
        'max_consecutive': mx,
        'verdict': 'PASS' if mx < n else 'FAIL',
        'threshold': f'最大连续重复 < {n} 词',
        'segments': segs[:10],
    })
    return result


def format_ngram(r):
    """把 ngram_check 的结果格式化为可读文本。"""
    out = [
        '=' * 56,
        'n-gram 防雷同校验',
        '=' * 56,
        f'新稿   : {r["tokens_new"]} tokens, 主导 {r.get("dominant_script_new", "?")}',
        f'对比稿 : {r["tokens_original"]} tokens, 主导 {r.get("dominant_script_original", "?")}',
        f'N      : {r["n"]}',
        '-' * 56,
    ]
    if r['cross_language_skip']:
        out += [f'判定   : SKIP（跨语种）', f'原因   : {r["reason"]}']
    else:
        out += [
            f'最大连续重复 : {r["max_consecutive"]} 词',
            f'判定         : {r["verdict"]}  ({r["threshold"]})',
        ]
        if r['segments']:
            out.append('-' * 56)
            out.append('重复片段 Top：')
            for s in r['segments'][:5]:
                out.append(f'  [{s["length"]} 词] {s["text"][:70]}')
    out.append('=' * 56)
    return '\n'.join(out)


# ==================================================================
# 二、合规自检（BLOCK / WARN / NOTE 三级）
# ==================================================================

# 审计区识别 —— 关键设计，别删。
# 踩过的坑：朴素全文扫描时，文档里「合规自检表」中**列举的禁用词本身**
# 会被当成违规命中（例如一行写「无绝对化用语（"永不掉色 / 第一 / 100%"）」，
# 会判 3 个 BLOCK）。实测误报率 >90%，精度这么低的工具比没有更糟，
# 人会很快学会无视它。因此默认开启审计区过滤：跳过元描述行，只扫真正的广告文案。
AUDIT_KEYWORDS = [
    '合规自检', '自检', '检查清单', '检查表', '检查项', '部署检查',
    '追踪部署', '追踪检查', 'Events API', 'Pixel', 'CAPI', 'UTM',
    '禁用', '规避', '已规避', '替代', '改用', '命中', '避雷', '占位符',
    '请替换', '慎用', '别用', '限流', '风险', '转化渠道', '首发推荐',
    'n-gram', '防雷同', '评分', '排序',
]

AUDIT_MARKS = ['\u2705', '\u26a0\ufe0f', '\u2611\ufe0f', '\u2610', '\u274c', '\u2611']

AUDIT_VERBS = ['无', '已', '未', '避免', '改用', '替代', '通过', '命中',
               '规避', '不出现', '全部', '均', '都是', '确认']

# 内置合规规则。需要行业定制时，改这里或传 custom_rules。
RULES = [
    {
        'tier': 'BLOCK', 'id': 'cta_no_shop', 'condition': 'no_shop',
        'banned_terms': ['小黄车', '购物车', 'Tap to buy', 'Buy now',
                         '点击购买', '立即下单', 'Add to cart'],
        'required_cta': 'Link in bio',
        'reason': '无小黄车时引导购物车内链路，属平台明确红线',
    },
    {
        'tier': 'BLOCK', 'id': 'absolute_claims',
        'banned_terms': ['最好', '第一', '唯一', '最闪', '永不掉色', '永不褪色',
                         '永久', '100%', '绝对', '全网最低', '史上最', '最佳'],
        'reason': '绝对化用语',
        'rewrite_rule': '改为可证伪的行为描述',
    },
    {
        'tier': 'WARN', 'id': 'soft_health_claims',
        'terms': ['防过敏', 'hypoallergenic', '医疗级', 'medical grade',
                  '纯天然', '无害'],
        'rewrite_rule': '降级为舒适度描述，或补充材质客观说明',
    },
    {
        'tier': 'WARN', 'id': 'health_efficacy',
        'terms': ['治疗', '保健', '治愈', '改善睡眠', '辟邪', '转运', '能量', '磁疗'],
        'rewrite_rule': '直接删除，功效/疗效宣称在多数平台属于高风险',
    },
]

# 未经核实的数字/承诺类声明。
# 注意：模式收得很紧，只匹配"像市场声明"的表述。
# 曾经用裸 `top \d+` 匹配，把文档里"Top 3 排名"（作者自己的变体排序）
# 误判成商品排名声明，已收紧。
UNVERIFIED_PATTERNS = [
    (r'\d[\d,，.]*\s*\+?\s*(?:reviews|review|评论|评价|好评)', '评论数/评价数声明'),
    (r'\d[\d,，.]*\s*\+?\s*(?:sold|sales|销量|已售|售出)', '销量声明'),
    (r'\d[\d,，.]*\s*\+?\s*(?:customers|顾客|客户|用户)\b', '客户数声明'),
    (r'(?:lifetime|终身|永久)\s*.{0,8}(?:warranty|guarantee|保色|保修|质保)',
     '终身保修/保色承诺'),
    (r'(?:排名第一|销量第一|销量冠军|行业第一|全网第一)', '排名声明'),
    (r'(?:#1\b|No\.?\s*1\b|number one|the #1)', '排名声明'),
    (r'(?:top[\s\-]?(?:rated|seller|selling))\b', '排名声明'),
    (r'\d(?:\.\d)?\s*(?:star|stars|星)\s*(?:rating|review)?', '评分声明'),
]


def _is_audit_line(line):
    """判断一行是否为元描述（审计/说明），而非实际广告文案。"""
    s = line.strip()
    if not s:
        return True
    if s.startswith('>'):
        return True
    if any(k in s for k in AUDIT_KEYWORDS):
        return True
    if any(m in s for m in AUDIT_MARKS) and any(v in s for v in AUDIT_VERBS):
        return True
    return False


def _find_hits(line, terms):
    """在单行内查找命中词，返回 [(term, 上下文)]"""
    hits = []
    low = line.lower()
    for t in terms:
        tl = t.lower()
        start = 0
        while True:
            idx = low.find(tl, start)
            if idx < 0:
                break
            ctx = line[max(0, idx - 25):idx + len(t) + 25].strip()
            hits.append((t, f'...{ctx}...'))
            start = idx + len(tl)
    return hits


def _check_unverified(line, whitelist):
    out = []
    for pat, label in UNVERIFIED_PATTERNS:
        for m in re.finditer(pat, line, flags=re.I):
            frag = m.group(0).strip()
            ctx = line[max(0, m.start() - 25):m.end() + 25].strip()
            covered = any(w.lower() in frag.lower() or frag.lower() in w.lower()
                          for w in whitelist)
            if not covered:
                out.append({
                    'claim': frag, 'label': label, 'context': f'...{ctx}...',
                    'action': '核实属实则补入 whitelist；否则删除或改为模糊表述',
                })
    return out


def compliance_check(text, has_shop_cart=False, whitelist=None,
                     custom_rules=None, audit_aware=True):
    """
    合规自检（BLOCK / WARN / NOTE 三级）。

    参数
        text          : 待检脚本正文。**只喂真正会投放的英文正文**，
                        不要把报告的中文界面标签一起塞进来，
                        「第一人称故事」这类角度名会被 absolute_claims 的「第一」误判 BLOCK。
        has_shop_cart : 是否有小黄车/Shop。为 False 时启用 cta_no_shop 规则。
        whitelist     : 品牌可证实声明白名单（字符串列表），用于豁免数字/承诺类声明。
        custom_rules  : 自定义规则列表，结构与 RULES 一致；传入则完全替代内置规则。
        audit_aware   : 是否开启审计区过滤，默认 True。关掉会全量扫描，误报很多。

    返回 dict，关键键：
        BLOCK / WARN / NOTE : 各级命中数
        findings            : 命中明细，按 (级别, 行号) 排序
        gate                : 'PASS' 或门禁提示
    """
    rules = custom_rules if custom_rules is not None else RULES
    rules = [r for r in rules
             if not (r.get('id') == 'cta_no_shop' and has_shop_cart)]
    whitelist = whitelist or []

    findings = []
    skipped = 0

    for lineno, raw in enumerate(text.splitlines(), 1):
        if audit_aware and _is_audit_line(raw):
            if any(k in raw for k in AUDIT_KEYWORDS) or \
               any(m in raw for m in AUDIT_MARKS):
                skipped += 1
            continue

        for r in rules:
            terms = r.get('banned_terms') or r.get('terms') or []
            for term, ctx in _find_hits(raw, terms):
                findings.append({
                    'tier': r['tier'], 'rule_id': r.get('id'),
                    'line': lineno, 'term': term, 'context': ctx,
                    'reason': r.get('reason', ''),
                    'rewrite_rule': r.get('rewrite_rule', ''),
                    'required_cta': r.get('required_cta', ''),
                })

        for u in _check_unverified(raw, whitelist):
            findings.append({
                'tier': 'BLOCK', 'rule_id': 'unverified_claims',
                'line': lineno, 'term': u['claim'], 'context': u['context'],
                'reason': f'{u["label"]} 未列入品牌声明白名单，无法核实',
                'rewrite_rule': u['action'], 'required_cta': '',
            })

    order = {'BLOCK': 0, 'WARN': 1, 'NOTE': 2}
    findings.sort(key=lambda f: (order.get(f['tier'], 9), f['line']))

    n_block = sum(1 for f in findings if f['tier'] == 'BLOCK')
    return {
        'rules_source': 'custom_rules' if custom_rules is not None else '内置通用规则',
        'has_shop_cart': has_shop_cart,
        'whitelist_size': len(whitelist),
        'audit_aware': audit_aware,
        'audit_lines_skipped': skipped,
        'BLOCK': n_block,
        'WARN': sum(1 for f in findings if f['tier'] == 'WARN'),
        'NOTE': sum(1 for f in findings if f['tier'] == 'NOTE'),
        'findings': findings,
        'gate': 'BLOCK 存在 -> 不得进入定稿' if n_block else 'PASS',
    }


def format_compliance(c):
    """把 compliance_check 的结果格式化为可读文本。"""
    out = [
        '=' * 62,
        '合规自检（BLOCK / WARN / NOTE）',
        '=' * 62,
        f'规则来源     : {c["rules_source"]}',
        f'小黄车       : {"有" if c["has_shop_cart"] else "无"}',
        f'白名单条目   : {c["whitelist_size"]}',
        f'审计区过滤   : {"开" if c["audit_aware"] else "关（全量扫描）"}',
        f'已跳过元描述 : {c["audit_lines_skipped"]} 行',
        '-' * 62,
        f'BLOCK {c["BLOCK"]}  |  WARN {c["WARN"]}  |  NOTE {c["NOTE"]}',
        '-' * 62,
    ]
    if not c['findings']:
        out.append('未命中任何规则。')
    for f in c['findings']:
        mark = {'BLOCK': '[BLOCK]', 'WARN': '[WARN ]',
                'NOTE': '[NOTE ]'}[f['tier']]
        out.append(f'{mark} L{f["line"]} - {f["rule_id"]} :: 「{f["term"]}」')
        out.append(f'          {f["context"]}')
        if f['reason']:
            out.append(f'          原因: {f["reason"]}')
        if f['rewrite_rule']:
            out.append(f'          改写: {f["rewrite_rule"]}')
        if f['required_cta']:
            out.append(f'          应改为: {f["required_cta"]}')
        out.append('')
    out += ['=' * 62, f'门禁判定: {c["gate"]}', '=' * 62]
    return '\n'.join(out)


# ==================================================================
# 自测：在 Code Interpreter 里执行本文件时会跑一遍，确认环境可用
# ==================================================================
if __name__ == '__main__':
    demo_new = ("I wore this necklace every single day for three months. "
                "It still looks brand new.")
    demo_old = ("I wore this necklace every single day for three months. "
                "It has not faded at all.")
    demo_ok = ("This chain has not faded on me after a full season of daily wear.")

    r1 = ngram_check(demo_new, demo_old)
    print(format_ngram(r1))
    print()
    r2 = ngram_check(demo_ok, demo_old)
    print(format_ngram(r2))
    print()

    demo_script = """Hook: The best jewelry you will ever own.
Body: Hypoallergenic and 100% safe. 10,000+ customers love it.
CTA: Tap to buy now.
"""
    c = compliance_check(demo_script, has_shop_cart=False)
    print(format_compliance(c))

