# -*- coding: utf-8 -*-
"""带调拼音 → 数字拼音（如 yuè → yue4）的小工具，纯 stdlib。
本仓自有代码，CC0（见 LICENSE.md）。"""
import re

_TONE_MAP = {}
for _base, _forms in {
    'a': 'āáǎà', 'e': 'ēéěè', 'i': 'īíǐì', 'o': 'ōóǒò', 'u': 'ūúǔù',
    'ü': 'ǖǘǚǜ', 'n': 'ńňǹ', 'm': 'ḿ', 'ê': 'ếề',
}.items():
    for _i, _ch in enumerate(_forms):
        _TONE_MAP[_ch] = (_base, _i + 1)
_TONE_MAP['ê'] = ('ê', 0)


def to_numbered(syllable: str) -> str:
    """单个带调音节转数字拼音；无调号按轻声处理，记 5。"""
    syllable = syllable.strip().lower().replace('ɡ', 'g')
    tone = 0
    out = []
    for ch in syllable:
        if ch in _TONE_MAP:
            base, t = _TONE_MAP[ch]
            out.append(base)
            if t:
                tone = t
        else:
            out.append(ch)
    return ''.join(out) + str(tone if tone else 5)


def split_readings(value: str):
    """Unihan kHanyuPinyin / kXHC1983 值：'loc:r1,r2 loc2:r3' → [r1, r2, r3]（带调原文）。"""
    res = []
    for tok in value.split():
        if ':' in tok:
            tok = tok.split(':', 1)[1]
        for r in tok.split(','):
            r = r.strip()
            if r:
                res.append(r)
    return res


_PINLU_RE = re.compile(r'^(.+?)\((\d+)\)$')


def parse_pinlu(value: str):
    """kHanyuPinlu 值：'lè(283) yuè(54)' → ([带调读音...], 最高频次)。"""
    readings, freq = [], 0
    for tok in value.split():
        m = _PINLU_RE.match(tok)
        if m:
            readings.append(m.group(1))
            freq = max(freq, int(m.group(2)))
    return readings, freq


def dedupe(seq):
    seen, out = set(), []
    for x in seq:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out
