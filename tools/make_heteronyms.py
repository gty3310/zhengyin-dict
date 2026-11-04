# -*- coding: utf-8 -*-
"""由《普通话异读词审音表》(1985) 生成 data/heteronyms.jsonl。
原件为国家语委、国家教委、广播电视部 1985-12-27 发布的规范文件（公共规范文本）；
解析用转录文本取自维基文库同名条目，条目数与 overtrue/pinyin-resources 所藏
PDF 原件（CC0 收集仓）标称的 839 条互校（见 SOURCES.md）。
结构：字头 [（一）读音（文/语）] 词例行（全角空格起、～为字头占位）/说明行 循环。
本脚本 CC0。"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pinyin_util import to_numbered

BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
WIKI = os.path.join(BASE, 'sources_raw', 'shenyinbiao_wikisource.txt')
OUT = os.path.join(BASE, 'data', 'heteronyms.jsonl')

_PINYIN = r'[a-züāáǎàēéěèīíǐìōóǒòūúǔùǖǘǚǜńňǹḿ]+'
_HEAD_RE = re.compile(
    r'^(?P<head>[\u4e00-\u9fff]{1,3}?)\s*'
    r'(?:（一）\s*)?(?P<py>' + _PINYIN + r')'
    r'(?:\s*（(?P<label>统读|文|语)）)?\s*(?P<rest>.*)$')
_SUB_RE = re.compile(
    r'^（(?P<idx>[一二三四五六七八九])）\s*(?P<py>' + _PINYIN + r')'
    r'(?:\s*（(?P<label>文|语)）)?\s*(?P<rest>.*)$')
_YOUYIN_RE = re.compile(r'又音\s*(' + _PINYIN + r')')


def clean_rest(rest: str):
    """字头/分读行尾的附注：去掉 <br/> 与脚注标记，余下作 note；另抽「又音」。"""
    rest = rest.replace('<br />', '').replace('<br/>', '').strip()
    rest = re.sub(r'\[[^\]]*\]', '', rest).strip()
    youyin = None
    m = _YOUYIN_RE.search(rest)
    if m:
        youyin = m.group(1)
        rest = _YOUYIN_RE.sub('', rest).strip(' ，,')
    return rest, youyin


def main():
    with open(WIKI, encoding='utf-8') as f:
        text = f.read()
    # 只取正文区：从 ==A== 到第一个脚注/分类标记
    m = re.search(r'==A==', text)
    body = text[m.start():] if m else text
    body = re.split(r'\[\[Category:', body)[0]
    lines = []
    for raw in body.splitlines():
        s = raw.strip()
        if not s or s.startswith('=='):
            continue
        if s.startswith('{{') or s.startswith('|'):
            continue
        lines.append(s)

    entries = []
    cur = None  # {'word':..., 'readings':[{pinyin,style,examples}], 'notes':[]}

    def flush():
        nonlocal cur
        if cur:
            note = '；'.join(cur['notes'])
            entries.append({
                'word': cur['word'],
                'readings': cur['readings'],
                'note': note,
                'src': 'shenyinbiao-1985',
                'src_ref': '维基文库转录/PDF原件藏 overtrue/pinyin-resources',
            })
            cur = None

    for s in lines:
        hm = _HEAD_RE.match(s)
        sm = _SUB_RE.match(s)
        if hm and not s.startswith('（'):
            flush()
            label = hm.group('label')
            cur = {'word': hm.group('head'), 'readings': [], 'notes': []}
            cur['readings'].append({
                'pinyin': to_numbered(hm.group('py')),
                'style': label if label in ('文', '语') else None,
                'examples': [],
            })
            if label == '统读':
                cur['notes'].append('统读')
            rest, youyin = clean_rest(hm.group('rest') or '')
            if youyin:
                cur['readings'].append({'pinyin': to_numbered(youyin), 'style': None, 'examples': []})
                cur['notes'].append('又音')
            if rest:
                cur['notes'].append(rest)
            continue
        if sm and cur is not None:
            cur['readings'].append({
                'pinyin': to_numbered(sm.group('py')),
                'style': sm.group('label'),
                'examples': [],
            })
            rest, _yy = clean_rest(sm.group('rest') or '')
            if rest:
                cur['notes'].append(rest)
            continue
        if cur is not None:
            content = s.replace('<br />', '').replace('<br/>', '').strip()
            if not content:
                continue
            if '～' in content:
                parts = [p.strip('　 。') for p in re.split(r'[\s　]+', content) if p.strip('　 。')]
                exs, rest = [], []
                for p in parts:
                    if p.startswith('～') or ('～' in p and len(p) <= 5):
                        # 一个 token 内可能连写两个词例（如 ～木林～姨），按 ～ 再切
                        subs = [q for q in re.split(r'(?=～)', p) if q]
                        exs += [q.replace('～', cur['word']) for q in subs]
                    else:
                        rest.append(p.replace('～', cur['word']))
                cur['readings'][-1]['examples'] += exs
                if rest:
                    cur['notes'].append(''.join(rest))
            else:
                cur['notes'].append(content)
    flush()

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, 'w', encoding='utf-8') as f:
        for r in entries:
            f.write(json.dumps(r, ensure_ascii=False) + '\n')
    print(f'heteronyms: {len(entries)} 条（审音表标称 839 条）')
    for r in entries[:2]:
        print(json.dumps(r, ensure_ascii=False))


if __name__ == '__main__':
    main()
