# -*- coding: utf-8 -*-
"""由北师大 tongjiazi-resources（MIT）生成 data/tongjia.jsonl。
取 tongjia_links.jsonl 全部关联（不按字合并：通假以 字+读音+义项 为键），
释义清洗为 sense，关联语料首条作 example、出处作 src_ref。
简体字段由 Unihan kSimplifiedVariant 生成，无映射留空。
许可证：MIT（见 LICENSES/ 与 SOURCES.md）。本脚本 CC0。"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pinyin_util import to_numbered

BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
RAW = os.path.join(BASE, 'sources_raw')
KB = os.path.join(RAW, 'tongjiazi-resources', 'kb', 'tongjia_links.jsonl')
YULIAO = os.path.join(RAW, 'tongjiazi-resources', 'kb', 'yuliao.jsonl')
OUT = os.path.join(BASE, 'data', 'tongjia.jsonl')

_TONG_SEG_RE = re.compile(r'[^。；]{0,4}?通\s*[“"\']\s*[^”"\']*?[”"\']\s*')
_XREF_RE = re.compile(r'^[“"\']\s*[^”"\']*?[”"\']\s*的[繁简]体字\s*[。．]*')


def clean_sense(raw: str, benzi: str) -> str:
    """源释义作「通“本字”。义项」或「义项。X，通“本字”」两种句式，剥掉通假标记段，只留义项。"""
    s = (raw or '').strip()
    s = _TONG_SEG_RE.sub('', s)
    s = _XREF_RE.sub('', s)
    return s.strip(' 。．')


def load_simp_map():
    simp = {}
    with open(os.path.join(RAW, 'Unihan_Variants.txt'), encoding='utf-8') as f:
        for line in f:
            if line.startswith('#') or '\t' not in line:
                continue
            cp, field, value = line.rstrip('\n').split('\t')
            if field == 'kSimplifiedVariant' and cp.startswith('U+'):
                simp[chr(int(cp[2:], 16))] = [chr(int(t[2:], 16)) for t in value.split() if t.startswith('U+')]
    return simp


def main():
    simp = load_simp_map()
    yuliao = {}
    with open(YULIAO, encoding='utf-8') as f:
        for line in f:
            if line.strip():
                c = json.loads(line)
                yuliao[c['语料ID']] = c
    out = []
    with open(KB, encoding='utf-8') as f:
        for line in f:
            if not line.strip():
                continue
            r = json.loads(line)
            char, benzi = r['通假字'], r['正字']
            example, src_ref = '', ''
            for cid in r.get('关联语料ID集合') or []:
                c = yuliao.get(cid)
                if c:
                    example = c.get('语料', '')
                    src_ref = c.get('出处', '')
                    break
            out.append({
                'char': char,
                'benzi': benzi,
                'reading': to_numbered(r['拼音']),
                'sense': clean_sense(r.get('释义', ''), benzi),
                'example': example,
                'char_simp': (simp.get(char) or [''])[0],
                'benzi_simp': (simp.get(benzi) or [''])[0],
                'src': 'tongjiazi-resources',
                'src_ref': src_ref,
            })
    out.sort(key=lambda r: (r['char'], r['reading'], r['benzi'], r['sense']))
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, 'w', encoding='utf-8') as f:
        for r in out:
            f.write(json.dumps(r, ensure_ascii=False) + '\n')
    with_ex = sum(1 for r in out if r['example'])
    print(f'tongjia: {len(out)} 条，带 example {with_ex} 条，带简体 {sum(1 for r in out if r["char_simp"])} 条')
    for r in out[:3]:
        print(json.dumps(r, ensure_ascii=False))


if __name__ == '__main__':
    main()
