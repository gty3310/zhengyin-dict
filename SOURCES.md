# 数据来源与加工说明（SOURCES）

本文件与每条记录的 `src` / `src_ref` 字段互为表里：`src` 标来源标识，
本文件记每个来源的出处、许可证、取了什么、做了什么加工、排除了什么。
构建日期 2026-11-04，数据版本 0.1.0。原始下载由 `tools/fetch_sources.sh` 复现，
原始文件不进 git（见 `.gitignore`）。

## 1. chars —— Unicode Unihan（`src: unihan:*`）

- 来源：Unicode 官方 UCD，`Unihan.zip`（https://www.unicode.org/Public/UCD/latest/ucd/Unihan.zip）
- 许可证：**Unicode License v3**（`LICENSES/Unicode-License-v3.txt`）
- 取用字段（`Unihan_Readings.txt` / `Unihan_Variants.txt`）：
  - `kMandarin` → `default`（该字最常用一读，即「字典默认读音」）
  - `kHanyuPinyin`、`kXHC1983` → `readings` 主体（全部读音，带调拼音转数字拼音）
  - `kHanyuPinlu` → 读音补充与频次序 `freq_rank`（按频次降序排名）
  - `kTGHZ2013` → `in_8105`（是否见于《通用规范汉字字典》2013，即通用规范汉字表体系）
  - `kSimplifiedVariant` → 简繁映射（供 tongjia 简体字段与异体互补用）
- 加工：
  1. 带调拼音统一转为数字拼音（`yuè` → `yue4`，轻声记 5）。
  2. **简繁异体互补**：同一字的简、繁两种字形在普通话中读音相同；当某字形自身
     缺 `kHanyuPinyin`/`kXHC1983` 时（如「說」），以其异体字形（「说」）的同字段
     补齐。发生过异体互补的记录在 `src_ref` 中标注 `incl. readings via variant`。
  3. `in_8105` 同样经异体传播：繁体字形若其简体对应形见于规范表，亦记为真——
     故 `in_8105` 的口径是「在通用规范汉字表收录范围内（含其繁体对应字形）」，
     条数（10,899）大于 8105 本身，属正常。
- 规模：44,569 字；其中 3,960 字带 `freq_rank`。

## 2. tongjia —— 北师大通假字资源库（`src: tongjiazi-resources`）

- 来源：frederick-wang/tongjiazi-resources（北京师范大学，CCL 2023 论文成果）
  https://github.com/frederick-wang/tongjiazi-resources
- 许可证：**MIT**（该仓 LICENSE、README、GitHub License 字段三处一致）
- 取用：知识库 `tongjia_links.jsonl` **全部 8,009 条**关联（不按字合并——见
  README「义项为键」）；语料库 `yuliao.jsonl` 按关联 ID 回连，取每条首个语料
  作 `example`、其出处作 `src_ref`（8,009 条全部带例）。
- 字段口径（重要）：
  - `reading` 取自源字段「拼音」——该拼音是**通假字在此条关联中的读音**，
    通假的常例是借字读本字之音，此拼音与本字读音一致；个别条目源数据给的
    是借字本读，使用者应以 `sense` 义项为准逐条核，别盲信。
    （抽查：随机 10 条的 reading/sense/example 相互对得上；典型如「共 gong1
    →供」多义项并列、「耗→眊 mao4·昏乱不明·《荀子·修身》例」均无误。）
  - `sense` 由源「释义」清洗：剥去「通“本字”。」标记段与「X，通“本字”」
    尾段、及「“X”的繁体字」交叉引用段，只留义项本身；源释义只有通假标记、
    无义项文字的 560 条，`sense` 留空待补。
  - 字头以繁体为主（源据《汉语大词典》凡例）；`char_simp` / `benzi_simp`
    由 Unihan `kSimplifiedVariant` 生成，无映射留空（3,189 条带简体）。
  - 源数据的「注音」「古音」字段未收入本表（TTS 定音用不到反切/注音符号）。
- 未取：标注语料 `corpus.jsonl` 与评测集未直接成表（语料已按 ID 回连为例句）。

## 3. heteronyms —— 《普通话异读词审音表》（1985）（`src: shenyinbiao-1985`）

- 来源：国家语言文字工作委员会、国家教育委员会、广播电视部 1985-12-27
  发布的规范文件（公共规范文本）。
- 获取与互校：解析文本取自维基文库同名条目转录；overtrue/pinyin-resources
  （CC0 收集仓）所藏 PDF 原件供条数互校——PDF 说明页自述全表规模，
  调研报告（本项目立项调研）记全表 839 条；本次结构化解析得 **829 条**，
  差额约 10 条为转录中版式特殊、机器解析未落条的条目，已列入待人工补录清单
  （见 README 路线图），不以估数充数。
- 加工：字头读音转数字拼音；分读的（文）/（语）标注入 `style`；词例中
  「～」回填字头；「统读」「又音」与行尾附注（如〔姓〕、义项范围注）入 `note`。
- 注意：本表审的是**现代**异读（如「说」只收 shuì 游说），**不收**文言破读
  （「说」yuè）——文言破读见 podu 表，两者不可互相替代。

## 4. phrases —— phrase-pinyin-data（`src: phrase-pinyin-data:<文件>`）

- 来源：mozillazg/phrase-pinyin-data（MIT）
  https://github.com/mozillazg/phrase-pinyin-data
- **只取三个文件**（逐文件溯源后确认权利链干净）：
  - `pinyin.txt`——基础词表；据该仓 README，其初始数据基于 phrases-dict.js
    与 pypinyin 的 phrases_dict（社区整理），**不是**汉典/CC-CEDICT 来源；
  - `overwrite.txt`——该项目手工纠正数据；
  - `di.txt`——该项目手工纠正「地」音短语数据。
- 加工：带调拼音转数字拼音；仅保留音节数与字数相等、全为汉字的行；
  同一（词，读音）去重，`src` 按 overwrite > di > pinyin 的优先级标最终来源。
  一词多音保留为多条记录。规模：53,995 条（词+读音组合）。

## 5. podu —— 本仓自建破读种子（`src: zhengyin-dict:podu-seed`，CC0）

- 性质：**AI 整理生成**（模型 Muse Wonder，2026-11-04），依据通行教材破读表
  与审音表词例，语境词例均取自《论语》《大学》《中庸》《孟子》等经典原文
  （个别取《诗经》《左传》及唐宋名篇）。每条按仓规带
  `gen: {by: "ai", model: "Muse Wonder", date: "2026-11-04"}` 与
  `verified: "unverified"`，`basis` 记依据类型、`confidence` 记置信度。
- 规模：65 条。宁缺毋滥：拿不准的条目未收入（如「衰 cuī」在《论语》中的
  落点存疑，未收）；个别读法有异说的（如「量 liang4」）标 `confidence: low`
  并在 basis 中注明。

## 排除清单（明确未并入）

| 被排除项 | 出处 | 理由 |
|---|---|---|
| `cc_cedict.txt`、`large_pinyin.txt` | phrase-pinyin-data 仓内 | 前者派生自 CC-CEDICT（**CC BY-SA 4.0**），后者为含前者与汉典数据的合并产物；SA 传染与本仓宽松方针冲突 |
| `zdic_cibs.txt`、`zdic_cybs.txt` | phrase-pinyin-data 仓内 | 汉典 zdic.net 抓取数据；汉典自身 CC0 宣告与其上游权利（BY-ND/BY-NC-ND）冲突，权利链不清 |
| pypinyin/pinyin-data 仓的 `cc_cedict.txt`、`zdic.txt` | mozillazg/pinyin-data | 同上两类——「仓库标 MIT」不等于每个文件都干净，逐文件切分后不用 |
| CC-CEDICT 本体 | cc-cedict.org / MDBG | CC BY-SA 4.0；计划作独立 BY-SA 数据包另行发布，不混编进本仓 |
| solos/pinyin-data 等无许可证仓库 | GitHub | 无 LICENSE 即默认版权保留，不得拆用 |

## 出处政策

- 五类 jsonl 的**每条**记录都带 `src`；能细化到条目级出处的另带 `src_ref`
  （如通假条的语料出处、chars 的字段构成）。
- AI 生成/整理的条目带 `gen` 与 `verified`，与权威源直采条目可按此筛选——
  筛选方法见 README「可信度分层」。
