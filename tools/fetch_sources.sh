#!/bin/sh
# 拉取全部原始数据源到 sources_raw/（该目录不进 git）。许可证细节见 SOURCES.md。
set -e
cd "$(dirname "$0")/../sources_raw"

# 1. Unicode Unihan（Unicode License v3）
curl -sL -o Unihan.zip "https://www.unicode.org/Public/UCD/latest/ucd/Unihan.zip"
unzip -o -q Unihan.zip

# 2. 北师大通假字资源库（MIT）；zip 解压密码见其 README
git clone -q --depth 1 https://github.com/frederick-wang/tongjiazi-resources.git || true
cd tongjiazi-resources
unzip -o -q -P BEIJING_NORMAL_UNIVERSITY knowledge_base/tongjiazi_knowledge_base.zip -d kb
cd ..

# 3. mozillazg/phrase-pinyin-data（MIT；仅用其中权利链干净的文件，见 tools/make_phrases.py）
git clone -q --depth 1 https://github.com/mozillazg/phrase-pinyin-data.git || true

# 4. 《普通话异读词审音表》(1985) 转录文本（维基文库）；
#    PDF 原件另藏于 overtrue/pinyin-resources（CC0 收集仓），供条数互校
curl -sL -A "zhengyin-dict build" \
  "https://zh.wikisource.org/w/index.php?title=%E6%99%AE%E9%80%9A%E8%AF%9D%E5%BC%82%E8%AF%BB%E8%AF%8D%E5%AE%A1%E9%9F%B3%E8%A1%A8&action=raw" \
  -o shenyinbiao_wikisource.txt
git clone -q --depth 1 https://github.com/overtrue/pinyin-resources.git || true

echo "sources ready in sources_raw/"
