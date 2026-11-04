# -*- coding: utf-8 -*-
"""把 data/*.jsonl 构建为 dist/zhengyin.db（SQLite）+ dist/manifest.json。
纯 Python stdlib。派生 substitutes 表：某读音 → 安全替字候选
（单音字、其默认读音恰为该音者优先；按 freq_rank、是否规范字表收录排序）。
带自检断言：条数下限、关键样本、出处字段齐全。自检不过则非零退出、不写 manifest。
本脚本 CC0。"""
import hashlib
import json
import os
import re
import sqlite3
import sys
from collections import defaultdict

BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
DATA = os.path.join(BASE, 'data')
DIST = os.path.join(BASE, 'dist')
VERSION = '0.1.0'
BUILT_AT = '2026-11-04'


def load(name):
    rows = []
    with open(os.path.join(DATA, name), encoding='utf-8') as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def unihan_version():
    try:
        with open(os.path.join(BASE, 'sources_raw', 'Unihan_Readings.txt'), encoding='utf-8') as f:
            head = ''.join(next(f) for _ in range(12))
        m = re.search(r'Unicode\s+(\d+\.\d+\.\d+)', head)
        return m.group(1) if m else 'latest'
    except Exception:
        return 'latest'


def main():
    chars = load('chars.jsonl')
    tongjia = load('tongjia.jsonl')
    heteronyms = load('heteronyms.jsonl')
    phrases = load('phrases.jsonl')
    podu = load('podu.jsonl')

    # ---- 自检：每条记录必须带 src ----
    for name, rows in [('chars', chars), ('tongjia', tongjia), ('heteronyms', heteronyms),
                       ('phrases', phrases), ('podu', podu)]:
        bad = [r for r in rows if not r.get('src')]
        assert not bad, f'{name} 有 {len(bad)} 条缺 src'

    # ---- 派生 substitutes ----
    by_reading = defaultdict(list)
    for r in chars:
        if len(r['readings']) == 1 and r['default'] == r['readings'][0]:
            by_reading[r['readings'][0]].append(r)
    substitutes = {}
    for reading, cand in by_reading.items():
        cand.sort(key=lambda r: (r['freq_rank'] is None, r['freq_rank'] or 0,
                                 not r['in_8105'], ord(r['char'])))
        substitutes[reading] = [r['char'] for r in cand[:30]]

    # ---- 关键样本断言 ----
    cmap = {r['char']: r for r in chars}
    assert 'yue4' in cmap['說']['readings'], '說 readings 应含 yue4'
    assert 'yue4' in cmap['樂']['readings'], '樂 readings 应含 yue4'
    tj = {(r['char'], r['reading'], r['benzi']) for r in tongjia}
    assert ('共', 'gong1', '供') in tj and ('共', 'gong1', '恭') in tj, '共 gong1 应既通供又通恭'
    assert '悦' in substitutes.get('yue4', []), 'yue4 替字候选应含单音字“悦”'
    assert all(r.get('gen', {}).get('by') == 'ai' and r.get('verified') == 'unverified' for r in podu), \
        'podu 每条须带 gen.by=ai 且 verified=unverified'

    counts = {'chars': len(chars), 'tongjia': len(tongjia), 'heteronyms': len(heteronyms),
              'phrases': len(phrases), 'podu': len(podu), 'substitutes': len(substitutes)}
    assert counts['chars'] >= 34000, counts
    assert counts['tongjia'] >= 8000, counts
    assert counts['heteronyms'] >= 700, counts
    assert counts['phrases'] >= 30000, counts
    assert counts['podu'] >= 60, counts
    assert counts['substitutes'] >= 1000, counts

    # ---- 写 SQLite ----
    os.makedirs(DIST, exist_ok=True)
    db_path = os.path.join(DIST, 'zhengyin.db')
    if os.path.exists(db_path):
        os.remove(db_path)
    con = sqlite3.connect(db_path)
    cur = con.cursor()
    cur.executescript('''
    CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT);
    CREATE TABLE chars (char TEXT PRIMARY KEY, readings TEXT NOT NULL, default_reading TEXT NOT NULL,
                        freq_rank INTEGER, in_8105 INTEGER NOT NULL, src TEXT NOT NULL, src_ref TEXT);
    CREATE TABLE tongjia (id INTEGER PRIMARY KEY, char TEXT NOT NULL, benzi TEXT NOT NULL,
                          reading TEXT NOT NULL, sense TEXT, example TEXT,
                          char_simp TEXT, benzi_simp TEXT, src TEXT NOT NULL, src_ref TEXT);
    CREATE INDEX idx_tongjia_char ON tongjia(char);
    CREATE TABLE heteronyms (word TEXT NOT NULL, readings TEXT NOT NULL, note TEXT,
                             src TEXT NOT NULL, src_ref TEXT);
    CREATE TABLE phrases (phrase TEXT NOT NULL, pinyin TEXT NOT NULL, src TEXT NOT NULL);
    CREATE INDEX idx_phrases_phrase ON phrases(phrase);
    CREATE TABLE podu (char TEXT NOT NULL, context TEXT, reading TEXT NOT NULL, sense TEXT,
                       basis TEXT, confidence TEXT, src TEXT NOT NULL, gen TEXT, verified TEXT);
    CREATE TABLE substitutes (reading TEXT PRIMARY KEY, candidates TEXT NOT NULL, src TEXT NOT NULL);
    ''')
    meta = {
        'name': 'zhengyin-dict', 'version': VERSION, 'built_at': BUILT_AT,
        'unihan_version': unihan_version(),
        'provenance_policy': 'every record carries src (item-level src_ref where available); '
                             'AI-generated records carry gen{by,model,date} and verified status',
    }
    cur.executemany('INSERT INTO meta VALUES (?,?)', sorted(meta.items()))
    cur.executemany('INSERT INTO chars VALUES (?,?,?,?,?,?,?)',
                    [(r['char'], json.dumps(r['readings'], ensure_ascii=False), r['default'],
                      r['freq_rank'], 1 if r['in_8105'] else 0, r['src'], r.get('src_ref', ''))
                     for r in chars])
    cur.executemany('INSERT INTO tongjia (char,benzi,reading,sense,example,char_simp,benzi_simp,src,src_ref)'
                    ' VALUES (?,?,?,?,?,?,?,?,?)',
                    [(r['char'], r['benzi'], r['reading'], r['sense'], r['example'],
                      r['char_simp'], r['benzi_simp'], r['src'], r.get('src_ref', '')) for r in tongjia])
    cur.executemany('INSERT INTO heteronyms VALUES (?,?,?,?,?)',
                    [(r['word'], json.dumps(r['readings'], ensure_ascii=False), r['note'],
                      r['src'], r.get('src_ref', '')) for r in heteronyms])
    cur.executemany('INSERT INTO phrases VALUES (?,?,?)',
                    [(r['phrase'], json.dumps(r['pinyin'], ensure_ascii=False), r['src']) for r in phrases])
    cur.executemany('INSERT INTO podu VALUES (?,?,?,?,?,?,?,?,?)',
                    [(r['char'], r['context'], r['reading'], r['sense'], r['basis'], r['confidence'],
                      r['src'], json.dumps(r.get('gen'), ensure_ascii=False), r.get('verified', ''))
                     for r in podu])
    cur.executemany('INSERT INTO substitutes VALUES (?,?,?)',
                    [(reading, json.dumps(cands, ensure_ascii=False), 'zhengyin-dict:derived-from-chars')
                     for reading, cands in substitutes.items()])
    con.commit()
    con.close()

    sha = hashlib.sha256(open(db_path, 'rb').read()).hexdigest()
    manifest = {
        'name': 'zhengyin-dict',
        'version': VERSION,
        'built_at': BUILT_AT,
        'unihan_version': meta['unihan_version'],
        'counts': counts,
        'sources': [
            {'id': 'unihan', 'license': 'Unicode License v3', 'used_for': 'chars'},
            {'id': 'tongjiazi-resources', 'license': 'MIT', 'used_for': 'tongjia'},
            {'id': 'shenyinbiao-1985', 'license': 'public normative document (1985)',
             'used_for': 'heteronyms'},
            {'id': 'phrase-pinyin-data', 'license': 'MIT', 'used_for': 'phrases (clean files only)'},
            {'id': 'zhengyin-dict:podu-seed', 'license': 'CC0', 'used_for': 'podu (AI-generated, unverified)'},
        ],
        'provenance_policy': meta['provenance_policy'],
        'db_file': 'zhengyin.db',
        'db_sha256': sha,
    }
    with open(os.path.join(DIST, 'manifest.json'), 'w', encoding='utf-8') as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    print('构建成功:', json.dumps(counts, ensure_ascii=False))
    print('db sha256:', sha)


if __name__ == '__main__':
    main()
