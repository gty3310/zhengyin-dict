# -*- coding: utf-8 -*-
"""由 mozillazg/phrase-pinyin-data（MIT）中权利链干净的文件生成 data/phrases.jsonl。
纳入：pinyin.txt（基础词表，据该仓 README 源自 phrases-dict.js 与 pypinyin
phrases_dict 的社区整理）、overwrite.txt（手工纠正）、di.txt（手工纠正「地」音）。
排除（见 SOURCES.md 排除清单）：cc_cedict.txt（CC BY-SA 衍生）、zdic_cibs.txt /
zdic_cybs.txt（汉典抓取、权利不清）、large_pinyin.txt（上述文件的合并产物）。
合并口径：同一（词，读音）去重，src 优先级 overwrite > di > pinyin。
许可证：MIT（见 LICENSES/ 与 SOURCES.md）。本脚本 CC0。"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pinyin_util import to_numbered

BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
SRC_DIR = os.path.join(BASE, 'sources_raw', 'phrase-pinyin-data')
OUT = os.path.join(BASE, 'data', 'phrases.jsonl')

FILES = [  # 低优先级在前，高优先级覆盖 src 标注
    ('pinyin.txt', 'phrase-pinyin-data:pinyin.txt'),
    ('di.txt', 'phrase-pinyin-data:di.txt'),
    ('overwrite.txt', 'phrase-pinyin-data:overwrite.txt'),
]


def parse_file(path):
    rows = []
    with open(path, encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#') or ':' not in line:
                continue
            phrase, _, rest = line.partition(':')
            rest = rest.split('#')[0].strip()
            phrase = phrase.strip()
            sylls = [to_numbered(s) for s in rest.split()]
            if len(sylls) != len(phrase) or not phrase:
                continue
            if not all('\u4e00' <= c <= '\u9fff' for c in phrase):
                continue
            rows.append((phrase, tuple(sylls)))
    return rows


def main():
    merged = {}
    for fname, src in FILES:
        for phrase, sylls in parse_file(os.path.join(SRC_DIR, fname)):
            merged[(phrase, sylls)] = src
    out = [{'phrase': p, 'pinyin': list(s), 'src': src}
           for (p, s), src in sorted(merged.items(), key=lambda kv: (kv[0][0], kv[0][1]))]
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, 'w', encoding='utf-8') as f:
        for r in out:
            f.write(json.dumps(r, ensure_ascii=False) + '\n')
    print(f'phrases: {len(out)} 条（词+读音组合），覆盖词 {len({r["phrase"] for r in out})} 个')


if __name__ == '__main__':
    main()
