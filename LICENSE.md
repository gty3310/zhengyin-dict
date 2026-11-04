# 许可证分工

本仓不是单一许可证——数据来自多个来源，各归其证。本文件说明分工；
逐项出处、链接与加工说明见 [SOURCES.md](SOURCES.md)，许可证原文见 `LICENSES/`。

| 内容 | 许可证 | 说明 |
|---|---|---|
| 本仓自建/自整理部分：`data/podu.jsonl`、`tools/` 全部脚本、文档 | **CC0 1.0** | 我方原创部分以 CC0 发布，可任意使用（含商用），无须署名 |
| `data/chars.jsonl`（源 Unicode Unihan） | **Unicode License v3** | 须保留 Unicode 版权与许可声明；原文见 `LICENSES/Unicode-License-v3.txt` |
| `data/tongjia.jsonl`（源 tongjiazi-resources，北京师范大学） | **MIT** | 保留其版权声明；原文见 `LICENSES/MIT.txt`，归属见 SOURCES.md |
| `data/phrases.jsonl`（源 phrase-pinyin-data 中权利链干净的文件） | **MIT** | 同上 |
| `data/heteronyms.jsonl`（源《普通话异读词审音表》1985） | 公共规范文本 | 1985 年国家语委、国家教委、广播电视部发布的规范文件；转录文本取自维基文库 |
| `dist/zhengyin.db`（发布版 SQLite） | 混合（同上逐表分工） | 每张表对应 jsonl 的许可证；`substitutes` 为由 chars 派生的索引，随 chars 的 Unicode License v3 |

**没有并入的数据**：CC-CEDICT 等 CC BY-SA 数据、汉典抓取数据、无许可证数据，
一律未进入本仓（清单与理由见 SOURCES.md「排除清单」）。CC-CEDICT 词组包
计划将来作为**独立的 BY-SA 数据包**另行发布，不与本仓混编。
