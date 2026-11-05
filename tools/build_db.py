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
VERSION = '0.3.1'
# v0.2.0 tongjia sense 草稿批次的期望计数（与发版报告一致，不一致即构建失败）
TONGJIA_SENSE_GEN_EXPECTED = 504
TONGJIA_SENSE_EMPTY_EXPECTED = 56
BUILT_AT = '2026-11-05'


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
    prescribed = load('prescribed.jsonl')

    # ---- 自检：每条记录必须带 src ----
    for name, rows in [('chars', chars), ('tongjia', tongjia), ('heteronyms', heteronyms),
                       ('phrases', phrases), ('podu', podu), ('prescribed', prescribed)]:
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
    # ---- common_readings 断言（v0.2.1 新增，源 kHanyuPinlu）----
    def common_of(c):
        return cmap[c].get('common_readings') or []
    assert 'wei2' in common_of('為') and 'wei4' in common_of('為'), '為 common 应含 wei2/wei4'
    assert 'xing1' in common_of('興'), '興 common 应含 xing1'
    assert 'hao4' in common_of('好'), '好 common 应含 hao4'
    assert 'wu4' in common_of('惡'), '惡 common 应含 wu4'
    assert 'bo2' in common_of('薄'), '薄 common 应含 bo2'
    assert 'xu4' in common_of('畜'), '畜 common 应含 xu4'
    assert 'yao4' not in common_of('樂'), '樂 common 不应含 yao4'
    assert common_of('乘') == ['cheng2'], '乘 common 应仅 cheng2'
    n_common = sum(1 for r in chars if r.get('common_readings'))
    assert n_common >= 3000, f'带 common_readings 字数 {n_common} < 3000'
    assert all(r.get('gen', {}).get('by') == 'ai' and r.get('verified') == 'unverified' for r in podu), \
        'podu 每条须带 gen.by=ai 且 verified=unverified'

    # ---- modern_readings 断言（v0.3.1 新增，源 kXHC1983 / kHanyuPinlu / kMandarin）----
    assert len(chars) == 44569, f'chars 总条数 {len(chars)} != 期望 44569'

    def modern_of(c):
        return cmap[c].get('modern_readings') or []
    assert set(modern_of('惡')) == {'e4', 'wu4'}, f"惡 modern 应为 {{e4, wu4}}，实得 {modern_of('惡')}"
    assert cmap['惡'].get('is_polyphonic') is True, '惡 is_polyphonic 应为 true'
    assert set(modern_of('好')) == {'hao3', 'hao4'}, f"好 modern 应为 {{hao3, hao4}}，实得 {modern_of('好')}"
    assert cmap['好'].get('is_polyphonic') is True, '好 is_polyphonic 应为 true'
    assert cmap['國'].get('unique_reading') == 'guo2', f"國 unique_reading 应为 guo2，实得 {cmap['國'].get('unique_reading')}"
    assert cmap['國'].get('is_polyphonic') is False, '國 is_polyphonic 应为 false'
    assert set(modern_of('為')) == {'wei2', 'wei4'}, f"為 modern 应为 {{wei2, wei4}}，实得 {modern_of('為')}"
    for r in chars:
        m = r.get('modern_readings') or []
        assert m, f"chars {r['char']} modern_readings 为空"
        assert r.get('modern_src') in ('xhc1983', 'pinlu', 'kmandarin-fallback'), \
            f"chars {r['char']} modern_src 非法: {r.get('modern_src')}"
        assert r.get('is_polyphonic') == (len(m) > 1), \
            f"chars {r['char']} is_polyphonic 与 modern_readings 长度不自洽"
        assert r.get('unique_reading') == (m[0] if len(m) == 1 else None), \
            f"chars {r['char']} unique_reading 与 modern_readings 不自洽"

    # ---- prescribed 断言（v0.3.0 新增）----
    assert len(prescribed) == 3, f'prescribed 条数 {len(prescribed)} != 期望 3'
    for r in prescribed:
        assert r.get('verified') == 'user_confirmed', f"prescribed 须 user_confirmed: {r}"
        if len(r['key']) == 1:
            sub = r['substitute']
            assert len(sub) == 1 and sub in cmap, f"prescribed 字级替字须为 chars 中单字: {r}"
            assert cmap[sub]['default'] == r['reading'], \
                f"prescribed 字级 {r['key']} 替字 {sub} 默认音 {cmap[sub]['default']} != {r['reading']}"
        else:
            syllables = r['reading'].split()
            assert len(r['substitute']) == len(syllables), \
                f"prescribed 短语 {r['key']} 替字字数与读音音节数不一致: {r}"
            for ch, syl in zip(r['substitute'], syllables):
                assert ch in cmap, f"prescribed 短语替字 {ch} 不在 chars: {r}"
                assert cmap[ch]['default'] == syl, \
                    f"prescribed 短语 {r['key']} 替字 {ch} 默认音 {cmap[ch]['default']} != {syl}"


    # ---- tongjia sense 批次断言（v0.2.0）----
    gen_rows = [r for r in tongjia if r.get('sense_gen')]
    empty_rows = [r for r in tongjia if not (r.get('sense') or '').strip()]
    assert len(gen_rows) == TONGJIA_SENSE_GEN_EXPECTED, \
        f'tongjia 带 sense_gen 条数 {len(gen_rows)} != 期望 {TONGJIA_SENSE_GEN_EXPECTED}'
    assert len(empty_rows) == TONGJIA_SENSE_EMPTY_EXPECTED, \
        f'tongjia sense 空缺 {len(empty_rows)} != 期望 {TONGJIA_SENSE_EMPTY_EXPECTED}'
    assert all((r.get('sense') or '').strip() and r['sense_gen'].get('by') == 'ai'
               and r.get('sense_verified') == 'unverified' for r in gen_rows), \
        'sense_gen 条目须 sense 非空、by=ai、sense_verified=unverified'
    sensed_orig = [r for r in tongjia if (r.get('sense') or '').strip() and not r.get('sense_gen')]
    assert all(not r.get('sense_verified') for r in sensed_orig), \
        '源自带 sense 的条目不应带 sense_verified 标记'

    counts = {'chars': len(chars), 'tongjia': len(tongjia), 'heteronyms': len(heteronyms),
              'phrases': len(phrases), 'podu': len(podu), 'prescribed': len(prescribed), 'substitutes': len(substitutes)}
    assert counts['chars'] >= 34000, counts
    assert counts['tongjia'] >= 8000, counts
    assert counts['heteronyms'] >= 700, counts
    assert counts['phrases'] >= 30000, counts
    assert counts['podu'] >= 60, counts
    assert counts['prescribed'] == 3, counts
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
                        freq_rank INTEGER, in_8105 INTEGER NOT NULL, src TEXT NOT NULL, src_ref TEXT,
                        common_readings TEXT, modern_readings TEXT, modern_src TEXT,
                        is_polyphonic INTEGER, unique_reading TEXT);
    CREATE TABLE tongjia (id INTEGER PRIMARY KEY, char TEXT NOT NULL, benzi TEXT NOT NULL,
                          reading TEXT NOT NULL, sense TEXT, example TEXT,
                          char_simp TEXT, benzi_simp TEXT, src TEXT NOT NULL, src_ref TEXT,
                          sense_gen TEXT, sense_verified TEXT);
    CREATE INDEX idx_tongjia_char ON tongjia(char);
    CREATE TABLE heteronyms (word TEXT NOT NULL, readings TEXT NOT NULL, note TEXT,
                             src TEXT NOT NULL, src_ref TEXT);
    CREATE TABLE phrases (phrase TEXT NOT NULL, pinyin TEXT NOT NULL, src TEXT NOT NULL);
    CREATE INDEX idx_phrases_phrase ON phrases(phrase);
    CREATE TABLE podu (char TEXT NOT NULL, context TEXT, reading TEXT NOT NULL, sense TEXT,
                       basis TEXT, confidence TEXT, src TEXT NOT NULL, gen TEXT, verified TEXT);
    CREATE TABLE prescribed ("key" TEXT NOT NULL, reading TEXT NOT NULL, substitute TEXT NOT NULL,
                             note TEXT, src TEXT NOT NULL, src_ref TEXT, verified TEXT);
    CREATE TABLE substitutes (reading TEXT PRIMARY KEY, candidates TEXT NOT NULL, src TEXT NOT NULL);
    ''')
    meta = {
        'name': 'zhengyin-dict', 'version': VERSION, 'built_at': BUILT_AT,
        'unihan_version': unihan_version(),
        'provenance_policy': 'every record carries src (item-level src_ref where available); '
                             'AI-generated records carry gen{by,model,date} and verified status',
    }
    cur.executemany('INSERT INTO meta VALUES (?,?)', sorted(meta.items()))
    cur.executemany('INSERT INTO chars VALUES (?,?,?,?,?,?,?,?,?,?,?,?)',
                    [(r['char'], json.dumps(r['readings'], ensure_ascii=False), r['default'],
                      r['freq_rank'], 1 if r['in_8105'] else 0, r['src'], r.get('src_ref', ''),
                      json.dumps(r.get('common_readings', []), ensure_ascii=False),
                      json.dumps(r.get('modern_readings', []), ensure_ascii=False),
                      r.get('modern_src', ''), 1 if r.get('is_polyphonic') else 0,
                      r.get('unique_reading'))
                     for r in chars])
    cur.executemany('INSERT INTO tongjia (char,benzi,reading,sense,example,char_simp,benzi_simp,src,src_ref,'
                    'sense_gen,sense_verified) VALUES (?,?,?,?,?,?,?,?,?,?,?)',
                    [(r['char'], r['benzi'], r['reading'], r['sense'], r['example'],
                      r['char_simp'], r['benzi_simp'], r['src'], r.get('src_ref', ''),
                      json.dumps(r['sense_gen'], ensure_ascii=False) if r.get('sense_gen') else '',
                      r.get('sense_verified', '')) for r in tongjia])
    cur.executemany('INSERT INTO heteronyms VALUES (?,?,?,?,?)',
                    [(r['word'], json.dumps(r['readings'], ensure_ascii=False), r['note'],
                      r['src'], r.get('src_ref', '')) for r in heteronyms])
    cur.executemany('INSERT INTO phrases VALUES (?,?,?)',
                    [(r['phrase'], json.dumps(r['pinyin'], ensure_ascii=False), r['src']) for r in phrases])
    cur.executemany('INSERT INTO podu VALUES (?,?,?,?,?,?,?,?,?)',
                    [(r['char'], r['context'], r['reading'], r['sense'], r['basis'], r['confidence'],
                      r['src'], json.dumps(r.get('gen'), ensure_ascii=False), r.get('verified', ''))
                     for r in podu])
    cur.executemany('INSERT INTO prescribed VALUES (?,?,?,?,?,?,?)',
                    [(r['key'], r['reading'], r['substitute'], r.get('note', ''),
                      r['src'], r.get('src_ref', ''), r.get('verified', '')) for r in prescribed])
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
            {'id': 'zhengyin-dict:tongjia-sense-ai-draft', 'license': 'CC0',
             'used_for': 'tongjia sense 草稿 504 条 (AI-generated, unverified; 字段级 sense_gen/sense_verified)'},
            {'id': 'user-ruling', 'license': 'CC0', 'used_for': 'prescribed (用户裁断指定替字, user_confirmed)'},
        ],
        'tongjia_sense': {'ai_drafted_unverified': len(gen_rows),
                          'still_empty': len(empty_rows)},
        'common_readings': {'derived_from': 'unihan:kHanyuPinlu',
                            'chars_covered': n_common,
                            'note': 'Pinlu 收录的读音即现代常用读音；CLI 据此判断目标音是否常用读音'},
        'modern_readings': {'derived_from': 'unihan:kXHC1983 ∩ (unihan:kHanyuPinlu ∪ {kMandarin default}); '
                                            'xhc 为空时取 kHanyuPinlu 本字读音，再空时取 kMandarin 默认音',
                            'chars_by_src': {s: sum(1 for r in chars if r.get('modern_src') == s)
                                             for s in ('xhc1983', 'pinlu', 'kmandarin-fallback')},
                            'polyphonic_chars': sum(1 for r in chars if r.get('is_polyphonic')),
                            'single_reading_chars': sum(1 for r in chars if not r.get('is_polyphonic')),
                            'note': '该字在现代汉语中的读音集；pinlu 只取本字本身读音，不用异体互补集合'},
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
