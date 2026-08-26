# -*- coding: utf-8 -*-
"""
清洗 book.txt 的 OCR 噪声，输出干净的正文 book_clean.txt：
1. 去掉封面/扉页/版权页/彩页目录/编委会/目录（第 1~16 页）
2. 去掉 Anna's Archive 元数据页（最后一页）
3. 去掉每页页眉（书名 / 第X章标题）和页码（独立纯数字行）
4. 去掉 OCR 垃圾行（连续句号、满屏标点）
5. 把断行合并成段落（按标题和句末断行分段）
"""
import re
from pathlib import Path

BASE = Path(__file__).parent
SRC = BASE / "book.txt"
OUT = BASE / "book_clean.txt"

text = SRC.read_text(encoding="utf-8")

# ===== 拆成 {页码: 内容} =====
parts = re.split(r'--- 第 (\d+) 页 ---', text)
pages = {}
for i in range(1, len(parts) - 1, 2):
    pages[int(parts[i])] = parts[i + 1].strip()

total = max(pages)
print(f"总页数: {total}")

# ===== 需要整页丢弃的 =====
FRONT_MATTER_END = 16          # 前 16 页是封面~目录
skip_pages = set(range(1, FRONT_MATTER_END + 1))

# Anna's Archive 元数据页（按内容识别，比只删最后一页更稳）
anna_pages = {n for n, c in pages.items()
              if "Anna's Archive" in c or "DuXiu collection" in c or "total_pages" in c}
skip_pages |= anna_pages

# ===== 单行噪声判断 =====
SENT_END = "。！？；：…"
HEADER_TITLE = "设施蔬菜水肥一体化栽培技术"

def is_header(line: str) -> bool:
    s = line.strip()
    if s == HEADER_TITLE:
        return True
    # 奇数页页眉是“第X章+章名”连在一起（如“第一章水肥一体化技术概述”）；
    # 单独的“第X章”是章标题页的章号，要保留，所以要求“章”后还有内容
    if re.match(r'^第[一二三四五六七八九十百]+章.', s):
        return True
    if s.startswith("SHESHI") or s.startswith("CHINA SCIENCE"):
        return True
    return False

def is_page_number(line: str) -> bool:
    return bool(re.fullmatch(r'\d{1,3}', line.strip()))

def is_garbage(line: str) -> bool:
    s = line.strip()
    if not s:
        return False
    if "。。" in s:                    # 正常文本不会出现连续句号
        return True
    if s.count("。") >= 5:             # 一行很少超过 5 个句号，否则是点线噪声
        return True
    # 几乎全是标点/符号，没有实质文字
    cjk = len(re.findall(r'[一-鿿]', s))
    alnum = len(re.findall(r'[A-Za-z0-9]', s))
    if cjk + alnum == 0 and len(s) >= 2:
        return True
    return False

def is_heading(line: str) -> bool:
    s = line.strip()
    if re.match(r'^第[一二三四五六七八九十百]+章', s):
        return True
    if re.match(r'^[一二三四五六七八九十]+、', s):
        return True
    if re.match(r'^[一二三四五六七八九十]+[）)]', s):
        return True
    if re.match(r'^[（(][一二三四五六七八九十]+[）)]', s):
        return True
    # 数字小标题（短行，如 "1." "2、"）
    if re.match(r'^\d+[.、]\s*', s) and len(s) < 40:
        return True
    return False

# ===== 逐页清洗 =====
cleaned_lines = []       # 清洗后的行（按页序）
skipped_page_nums = sorted(skip_pages)

for n in range(1, total + 1):
    if n in skip_pages:
        continue
    content = pages.get(n, "")
    for raw in content.split("\n"):
        line = raw.strip()
        if not line:
            continue
        if is_header(line) or is_page_number(line) or is_garbage(line):
            continue
        cleaned_lines.append(line)

# ===== 合并断行为段落 =====
paragraphs = []
cur = ""
for line in cleaned_lines:
    if is_heading(line):
        if cur:
            paragraphs.append(cur)
            cur = ""
        paragraphs.append(line)          # 标题单独成段
        continue
    # 上一行是短行且以句末标点结尾 → 很可能是段落末行，断开
    if cur and len(cur) <= 15 and cur[-1] in SENT_END:
        paragraphs.append(cur)
        cur = line
    else:
        cur = (cur + line) if cur else line

if cur:
    paragraphs.append(cur)

# ===== 去重：OCR 拆行的页眉会留下重复的“第X章”（每章标题只该出现一次）=====
def is_chapter_name(p: str) -> bool:
    s = p.strip()
    return 0 < len(s) < 18 and not re.search(r'[。！？；：，、]', s)

seen_chapters = set()
final_paragraphs = []
i = 0
while i < len(paragraphs):
    p = paragraphs[i]
    s = p.strip()
    m = re.fullmatch(r'第([一二三四五六七八九十]+)章', s)
    if m and m.group(1) in seen_chapters:
        # 重复章号 = 拆行页眉，删掉；若下一段是短章名（页眉另一半）也一并删
        if i + 1 < len(paragraphs) and is_chapter_name(paragraphs[i + 1]):
            i += 1
        i += 1
        continue
    if m:
        seen_chapters.add(m.group(1))
    final_paragraphs.append(p)
    i += 1

paragraphs = final_paragraphs

result = "\n\n".join(paragraphs) + "\n"
OUT.write_text(result, encoding="utf-8")

print(f"丢弃整页: {len(skip_pages)} 页 (前 {FRONT_MATTER_END} 页 + {sorted(anna_pages)})")
print(f"清洗后行数: {len(cleaned_lines)} -> 段落数: {len(paragraphs)}")
print(f"输出: {OUT} ({len(result)} 字符)")
