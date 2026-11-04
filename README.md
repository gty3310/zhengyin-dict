# zhengyin-dict · 古文正音字典

一份为「古文 AI 朗读定音」而建的开放字典数据：给定一篇古文，它回答四件事——
每个字有哪些读音、**默认会读成什么音**、在具体语境里**应该读什么音**（词组、
通假、异读、破读）、以及某个音有哪些**可安全替换的同音字**。

它是 [zhengyin](https://github.com/gty3310) 正音工具链的数据仓，与 CLI 代码仓分离：
本仓只有数据（人可读的 JSONL + 发布版 SQLite），任何人都可以直接取用这份字典
做自己的工具，也可以提 PR 补条目。许可证按来源分工（见 [LICENSE.md](LICENSE.md)），
其中本仓自建部分以 **CC0** 发布、明确允许商用。

当前版本 **0.3.0**（2026-11-04）：

| 表 | 条数 | 内容 |
|---|---|---|
| chars | 44,569 | 单字全部读音 + 默认读音 + 频次序 |
| phrases | 53,995 | 词组逐字拼音（多音消歧） |
| tongjia | 8,009 | 通假关系（字+读音+义项 → 本字），全带出处例句 |
| heteronyms | 829 | 《普通话异读词审音表》(1985) 现代异读 |
| podu | 65 | 文言破读种子（自建，AI 整理，未核验） |
| prescribed | 3 | 指定替字（用户裁断，`user_confirmed`） |
| substitutes（派生） | 1,332 个读音 | 每音的安全同音替字候选 |

## 数据与字段

数据以 JSONL 存放在 `data/`，每行一条 JSON。拼音一律为**数字拼音**
（`yue4`，轻声记 5）。**每条记录都带 `src` 出处字段**，能细化到条目级的另带
`src_ref`；具体来源与加工见 [SOURCES.md](SOURCES.md)。

### chars.jsonl — 单字读音

```json
{"char": "說", "readings": ["shuo1", "shui4", "yue4"], "default": "shuo1",
 "freq_rank": 27, "in_8105": true, "src": "unihan:kXHC1983", "src_ref": "…"}
```

- `readings`：全部读音（源 Unihan kHanyuPinyin / kXHC1983，简繁异体互补）
- `default`：字典默认读音（kMandarin）——判断「原样送 TTS 会不会读错」的基准
- `freq_rank`：kHanyuPinlu 频次排名（越小越常用；无频次数据为 `null`）
- `common_readings`：现代常用读音集（源 kHanyuPinlu 收录的全部读音，含异体互补；Pinlu 未收录的字为空表）
- `in_8105`：是否在《通用规范汉字表》收录范围内（含繁体对应字形）

### phrases.jsonl — 词组消歧

```json
{"phrase": "中国", "pinyin": ["zhong1", "guo2"], "src": "phrase-pinyin-data:pinyin.txt"}
```

`pinyin` 与 `phrase` 逐字对齐；一词多音有多条记录。

### tongjia.jsonl — 通假（义项为键）

```json
{"char": "共", "benzi": "供", "reading": "gong1", "sense": "供奉，贡献",
 "example": "繼統共勤，順皇之德。", "char_simp": "", "benzi_simp": "",
 "src": "tongjiazi-resources", "src_ref": "《汉书·礼乐志》"}
```

字段与设计见下方「义项为键」一节。源：北师大通假字资源库（MIT）。

### heteronyms.jsonl — 现代异读（审音表 1985）

```json
{"word": "薄", "readings": [{"pinyin": "bao2", "style": "语", "examples": ["纸很薄"]},
 {"pinyin": "bo2", "style": "文", "examples": ["薄弱", "单薄"]}],
 "note": "", "src": "shenyinbiao-1985", "src_ref": "…"}
```

`style` 为审音表原注的「文/语」；`note` 含「统读」「又音」等附注。
注意：本表只管现代异读，不收文言破读（如「说 yuè」在 podu 表）。

### podu.jsonl — 文言破读（自建种子）

```json
{"char": "说", "context": "《论语·学而》「学而时习之，不亦说乎」", "reading": "yue4",
 "sense": "通“悦”，喜悦", "basis": "教材破读表", "confidence": "high",
 "src": "zhengyin-dict:podu-seed",
 "gen": {"by": "ai", "model": "Muse Wonder", "date": "2026-11-04"},
 "verified": "unverified"}
```

`context` 是经典原文语境词例，`sense` 是一句义项说明。**这一层是 AI 整理的
种子，未经人工核验**（见「可信度分层」）。

### prescribed.jsonl — 指定替字（用户裁断）

```json
{"key": "緡", "reading": "mian2", "substitute": "绵", "note": "緡蠻即綿蠻，綿音義雙合；替字索引按字頻誤選棉，用戶裁定改綿", "src": "user-ruling", "src_ref": "2026-11-04 用户裁断", "verified": "user_confirmed"}
```

用户裁断的指定替字：当某个字（或短语）在指定读音下必须换成指定的替字时，
以此表为准。**优先级高于通假与 substitutes 替字索引**——下游工具遇
`key`＋`reading` 命中本表时，直接用 `substitute`，不再走自动候选。

- `key`：原字或原短语（单字为字级条目，多字为短语条目）
- `reading`：目标读音，数字拼音；短语以空格分隔、逐字对齐（如 `wu1 hu1`）
- `substitute`：指定替字或替词；构建时断言校验——字级条目的替字须在
  chars 表中且其默认读音恰为 `reading`，短语条目逐字核默认读音与各音节相等
- `note`：裁断理由
- `src` / `src_ref`：固定为 `user-ruling` 与裁断日期出处
- `verified`：固定为 `user_confirmed`

暂缓条目：原计划的「迸 bǐng → 摒」未写入本表——摒在字表中
`readings=[bing4, bing3]`、默认音为 bing4 但并非单音字，另有冷僻读音
bing3，未达指定替字的单音标准，暂缓待用户裁。

### substitutes（仅在 SQLite 中，构建时派生）

`reading → [安全替字…]`：候选限定为「单音字且其默认读音恰为该音」的字
——把目标字换成它，任何按默认读音工作的 TTS 都不会读错；按 `freq_rank`、
是否规范字表收录排序。如 `yue4 → 悦、阅、岳、粤…`。

## 两种用法

**一、直接读 JSONL**：`data/*.jsonl` 即全部数据，任何语言可读，不需要构建。

**二、用发布版 SQLite**：GitHub Release 附 `zhengyin.db` 与 `manifest.json`
（manifest 含各表条数、源清单与 db 的 sha256）。表结构与 jsonl 一一对应，
另有 `substitutes` 与 `meta` 表。本地重建：

```bash
python3 tools/fetch_sources.sh   # 拉原始数据到 sources_raw/（不进 git）
python3 tools/make_chars.py && python3 tools/make_tongjia.py
python3 tools/make_heteronyms.py && python3 tools/make_phrases.py
python3 tools/make_podu.py
python3 tools/build_db.py        # 产出 dist/zhengyin.db + manifest，带断言自检
```

## 可信度分层

每条记录都可按可信度筛选，请按你的用途取舍：

| 层级 | 识别方法 | 含义 |
|---|---|---|
| 权威源直采 | `src` 为 `unihan:*` / `tongjiazi-resources` / `shenyinbiao-1985` / `phrase-pinyin-data:*` | 直接来自权威或已核实的开放数据源，加工过程可复现（见 SOURCES.md） |
| AI 生成未核 | 带 `gen: {"by": "ai", …}` 且 `verified: "unverified"` | 由 AI 整理/生成，未经人工核验——**只可作提示，不可作定论**（podu 种子属此类；tongjia 的 504 条 `sense` 草稿同理，但标记是字段级的 `sense_gen` / `sense_verified`，见下） |
| 人工已核 | `verified: "human_checked"` | 经人工逐条核过（目前尚无此层条目，等待贡献者核验 podu 后产生） |

**给下游 CLI 的默认政策方向**：自动替换只能使用「权威源直采」与「人工已核」
条目；AI 未核条目只作向用户提问时的提示与候选，绝不直接落字。

## 义项为键

通假关系不是「字→字」，而是「**字＋读音＋义项→本字**」：同一个通假字在不同
义项下通不同的本字，同字同音也可能通两三个本字。本仓实例：「共」gōng 既通
「供」（供奉、供给、供养……各为一条），也通「恭」（恭敬、恭肃……）。所以：

- tongjia 表的唯一键按 **(char, reading, sense)** 理解，同字多条并列保存，
  永不按字合并；每条尽量带 `sense` 与 `example`（出处例句）。源释义无义项
  文字的 560 条中，504 条已由 AI 依据例句起草 `sense`（v0.2.0，带字段级
  `sense_gen` 标记、`sense_verified: "unverified"`，待人工核验），余
  56 条继续留空待补。
- podu 表同理：每条带 `context` 语境词例与一句 `sense`。

**给下游 CLI 的政策方向**：通假替换优先换**本字**，做到音、义双对；同字同音
出现多个本字竞争时，把各义项列出来让 Agent/用户按上下文选，不擅自合并定音。
更进一步，转换以「音义双合」为纲：凡字典里有带义项映射的条目（通假、破读、
语境异读），即便原字读音不算错，也尽量换成本字——因为现代 TTS 按语义定读音
与韵律，语义不通的替字会让朗读别扭。

## 如何贡献

欢迎 PR 补条目，尤其是：podu 破读新条、tongjia 余下 56 条 `sense`
空缺补全、tongjia 504 条 AI 草稿 `sense` 的人工核验、heteronyms 未落条
的约 10 条、podu 现有条目的人工核验（核过请把 `verified` 改为
`human_checked` 并在 PR 里说明依据；tongjia 草稿核过请把该条
`sense_verified` 改为 `human_checked`）。

硬性要求：**每条新条目必须带出处**——

- 补 podu：照现有格式，`basis` 写明依据（教材名/审音表词例/注疏出处），
  `context` 必须是真实经典原文，不许编造；AI 代笔的条目必须保留
  `gen` 标记与 `verified: "unverified"`，不得冒充人工核验。
- 补 tongjia sense：义项须能溯源到词典或原书注疏，在 PR 描述里给出处。
- 改 chars/phrases/heteronyms：这三类是脚本从上游生成的，请改 `tools/`
  的加工脚本或向上游提报，不要手改 jsonl（会被下次构建覆盖）。

## 版本规则

数据版本用 SemVer：条目增补 → 次版本（0.2.0）；字段结构变更 → 主版本；
纯错漏修正 → 修订号。每次发版更新 `dist/manifest.json` 的条数与 sha256，
并在 GitHub Release 附 db 文件。本仓代码（tools/）与文档为 CC0。

## 路线图

- tongjia 的 504 条 AI 草稿 `sense` 待人工逐条核验升档
  （`sense_verified: "human_checked"`）；余 56 条空缺待人工补全；
- heteronyms 未落条约 10 条的人工补录；
- podu 破读表长期生长：靠人工贡献与下游 CLI「问答学习回路」回流
  （用户答、算法校验、人工核后入库）；
- 教材口径的常用通假校验层（约 120–270 条）自建补入；
- CC-CEDICT 词组包将作为**独立的 CC BY-SA 数据包**另行发布，可选装，
  永不混编进本仓。
