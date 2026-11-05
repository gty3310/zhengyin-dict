# -*- coding: utf-8 -*-
"""由 Unicode Unihan 生成 data/chars.jsonl。
来源字段：kMandarin(默认读音) / kHanyuPinyin(全读音) / kXHC1983(全读音) /
kHanyuPinlu(频次序) / kTGHZ2013(通用规范汉字表收录标记)。
加工：简繁异体字（kSimplifiedVariant 及其逆映射）之间互补读音——同一字的
简繁两种字形在普通话中读音相同，主字段缺失时以异体字字段补齐，出处仍为 Unihan。
现代读音三字段（v0.3.1 新增：modern_readings / modern_src，另派生
is_polyphonic / unique_reading）：设 xhc＝本字 kXHC1983 读音集、
pinlu＝本字 kHanyuPinlu 读音集（只用本字本身，不用异体互补后的集合）、
default＝本条 default（kMandarin 默认音）。
1) xhc 非空：modern＝xhc ∩ (pinlu ∪ {default})，交集为空则 modern＝xhc，
   modern_src＝xhc1983（1983 词典里个别读音只存于古义/旧读，须经现代
   频次实测过滤，如「惡」的 ě/wū 即如此滤掉）；
2) xhc 空、pinlu 非空：modern＝pinlu，modern_src＝pinlu；
3) 皆空：modern＝[default]，modern_src＝kmandarin-fallback。
列表顺序：default 在集内时排第一，其余按 xhc（或 pinlu）原始顺序。
is_polyphonic＝len(modern)>1；unique_reading＝len 恰 1 时为该读音、否则 null。
许可证：Unicode License v3（见 LICENSES/ 与 SOURCES.md）。本脚本 CC0。"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pinyin_util import to_numbered, split_readings, parse_pinlu, dedupe

RAW = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'sources_raw')
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'chars.jsonl')

FIELDS = ('kMandarin', 'kHanyuPinyin', 'kXHC1983', 'kHanyuPinlu', 'kTGHZ2013')


def load_readings():
    data = {}
    with open(os.path.join(RAW, 'Unihan_Readings.txt'), encoding='utf-8') as f:
        for line in f:
            if line.startswith('#') or '\t' not in line:
                continue
            cp, field, value = line.rstrip('\n').split('\t')
            if field in FIELDS and cp.startswith('U+'):
                data.setdefault(chr(int(cp[2:], 16)), {})[field] = value
    return data


def load_variants():
    simp = {}
    with open(os.path.join(RAW, 'Unihan_Variants.txt'), encoding='utf-8') as f:
        for line in f:
            if line.startswith('#') or '\t' not in line:
                continue
            cp, field, value = line.rstrip('\n').split('\t')
            if field == 'kSimplifiedVariant' and cp.startswith('U+'):
                simp[chr(int(cp[2:], 16))] = [chr(int(t[2:], 16)) for t in value.split() if t.startswith('U+')]
    trad = {}
    for t, ss in simp.items():
        for s in ss:
            trad.setdefault(s, []).append(t)
    return simp, trad


def main():
    data = load_readings()
    simp, trad = load_variants()

    def counterparts(ch):
        out = []
        out += simp.get(ch, [])
        out += trad.get(ch, [])
        return out

    def own_xhc(ch):
        """本字 kXHC1983 读音集（数字拼音，有序去重；不用异体互补）。"""
        v = data.get(ch, {}).get('kXHC1983')
        return dedupe([to_numbered(r) for r in split_readings(v)]) if v else []

    def own_pinlu(ch):
        """本字 kHanyuPinlu 读音集（数字拼音，有序去重；不用异体互补）。"""
        v = data.get(ch, {}).get('kHanyuPinlu')
        if not v:
            return []
        rs, _freq = parse_pinlu(v)
        return dedupe([to_numbered(r) for r in rs])

    def derive_modern(ch, default):
        """按文件头派生规则返回 (modern_readings, modern_src)。"""
        xhc = own_xhc(ch)
        pinlu = own_pinlu(ch)
        if xhc:
            allow = set(pinlu) | {default}
            inter = [r for r in xhc if r in allow]
            modern = inter if inter else list(xhc)
            order_src = xhc
            src_m = 'xhc1983'
        elif pinlu:
            modern = list(pinlu)
            order_src = pinlu
            src_m = 'pinlu'
        else:
            return [default], 'kmandarin-fallback'
        rest = [r for r in order_src if r in set(modern) and r != default]
        ordered = ([default] if default in modern else []) + rest
        for r in modern:
            if r not in ordered:
                ordered.append(r)
        return ordered, src_m

    def raw_readings(ch):
        """返回 (带调读音有序表, 用到的字段集合, pinlu最高频次, pinlu读音表)。"""
        d = data.get(ch, {})
        fields, readings = set(), []
        if 'kHanyuPinyin' in d:
            readings += split_readings(d['kHanyuPinyin'])
            fields.add('kHanyuPinyin')
        if 'kXHC1983' in d:
            readings += split_readings(d['kXHC1983'])
            fields.add('kXHC1983')
        pinlu_freq, pinlu_readings = 0, []
        if 'kHanyuPinlu' in d:
            pinlu_readings, pinlu_freq = parse_pinlu(d['kHanyuPinlu'])
            readings += pinlu_readings
            fields.add('kHanyuPinlu')
        return readings, fields, pinlu_freq, pinlu_readings

    records = {}
    pinlu_freq_of = {}
    for ch in sorted(set(data) | set(simp) | set(trad)):
        own, used, pf, own_pinlu_list = raw_readings(ch)
        allr = list(own)
        pinlu_all = list(own_pinlu_list)
        via_variant = False
        for cp in counterparts(ch):
            cr, cf, cpf, cpinlu = raw_readings(cp)
            if cf:
                via_variant = True
            allr += cr
            pinlu_all += cpinlu
            used |= cf
            pf = max(pf, cpf)
        mand = data.get(ch, {}).get('kMandarin')
        if not mand:
            for cp in counterparts(ch):
                mand = data.get(cp, {}).get('kMandarin')
                if mand:
                    via_variant = True
                    break
        if mand:
            used.add('kMandarin')
            allr.append(mand.split()[0])
        readings = dedupe([to_numbered(r) for r in allr if r])
        if not readings:
            continue
        default = to_numbered(mand.split()[0]) if mand else readings[0]
        if default not in readings:
            readings.insert(0, default)
        in8105 = 'kTGHZ2013' in data.get(ch, {}) or any('kTGHZ2013' in data.get(cp, {}) for cp in counterparts(ch))
        if 'kHanyuPinyin' in used:
            src = 'unihan:kHanyuPinyin'
        elif 'kXHC1983' in used:
            src = 'unihan:kXHC1983'
        else:
            src = 'unihan:kMandarin'
        src_ref = ','.join(sorted(used))
        if via_variant:
            src_ref += '; incl. readings via simplified/traditional variant'
        modern_readings, modern_src = derive_modern(ch, default)
        records[ch] = {
            'char': ch,
            'readings': readings,
            'common_readings': dedupe([to_numbered(r) for r in pinlu_all if r]),
            'default': default,
            'modern_readings': modern_readings,
            'modern_src': modern_src,
            'is_polyphonic': len(modern_readings) > 1,
            'unique_reading': modern_readings[0] if len(modern_readings) == 1 else None,
            'freq_rank': None,
            'in_8105': in8105,
            'src': src,
            'src_ref': src_ref,
        }
        if pf:
            pinlu_freq_of[ch] = pf

    ranked = sorted(pinlu_freq_of.items(), key=lambda kv: (-kv[1], ord(kv[0])))
    for i, (ch, _pf) in enumerate(ranked, 1):
        records[ch]['freq_rank'] = i

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, 'w', encoding='utf-8') as f:
        for ch in sorted(records, key=ord):
            f.write(json.dumps(records[ch], ensure_ascii=False) + '\n')
    n_common = sum(1 for r in records.values() if r['common_readings'])
    print(f'chars: {len(records)} 条，带 freq_rank {len(ranked)} 条，in_8105 {sum(r["in_8105"] for r in records.values())} 条，带 common_readings {n_common} 条')
    for s in ('xhc1983', 'pinlu', 'kmandarin-fallback'):
        print(f'modern_src={s}: {sum(1 for r in records.values() if r["modern_src"] == s)} 字')
    print(f'modern 多音字 {sum(1 for r in records.values() if r["is_polyphonic"])} 字，单音字 {sum(1 for r in records.values() if not r["is_polyphonic"])} 字')


if __name__ == '__main__':
    main()
