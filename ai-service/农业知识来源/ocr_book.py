# -*- coding: utf-8 -*-
"""
扫描版 PDF 转文字：
1. PDF 每页转图片
2. 逐张调百度 OCR（通用文字识别·标准版）
3. 合并成 book.txt
"""
import base64
import sys
import time
import requests
import fitz  # PyMuPDF
from pathlib import Path

# Windows 控制台默认 GBK 编码，打印 emoji 会崩，统一转成 UTF-8
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

# ===== ① 配置（改这两行 + 可选页码范围）=====
API_KEY = "Bn7qCcy6ndL1pUFcUik3ZF8h"
SECRET_KEY = "ItlQF8NtUVugwAg4KM3jTtOPVkB56zxz"
START_PAGE = 1    # 从第几页开始（1 起）
END_PAGE = 0      # 到第几页结束（0 = 一直到最后）
DPI_ZOOM = 2.8    # 约 200 DPI，够清晰

# ===== ② 自动找 PDF（脚本和 PDF 放同一文件夹）=====
BASE = Path(__file__).parent
pdfs = sorted(BASE.glob("*.pdf"))
if not pdfs:
    print("❌ 没找到 PDF，请把脚本和 PDF 放同一文件夹")
    exit(1)
PDF = pdfs[0]
print(f"📄 找到 PDF: {PDF.name}")


def get_access_token():
    """用 API Key + Secret Key 换 access_token（有效期约30天）"""
    url = "https://aip.baidubce.com/oauth/2.0/token"
    params = {
        "grant_type": "client_credentials",
        "client_id": API_KEY,
        "client_secret": SECRET_KEY,
    }
    r = requests.post(url, params=params, timeout=30)
    data = r.json()
    if "access_token" in data:
        return data["access_token"]
    print("❌ 获取 access_token 失败，请检查 API Key / Secret Key:", data)
    exit(1)


def ocr_image(img_bytes, token):
    """把一张图发给百度 OCR，返回识别出的文字"""
    url = "https://aip.baidubce.com/rest/2.0/ocr/v1/general_basic"
    payload = {
        "access_token": token,
        "image": base64.b64encode(img_bytes).decode(),
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    for attempt in range(3):  # 失败重试 3 次
        try:
            r = requests.post(url, data=payload, headers=headers, timeout=30)
            data = r.json()
            if "words_result" in data:
                return "\n".join(w["words"] for w in data["words_result"])
            if "error_code" in data:
                code = data["error_code"]
                print(f"   ⚠️ OCR 错误 {code}: {data.get('error_msg')}")
                if code in (17, 18):  # 额度/QPS 超限，等 3 秒再试
                    time.sleep(3)
                    continue
                return ""
        except Exception as e:
            print(f"   ⚠️ 请求异常: {e}")
            time.sleep(2)
    return ""


def main():
    token = get_access_token()
    doc = fitz.open(PDF)
    total = doc.page_count
    end = END_PAGE if END_PAGE > 0 else total
    print(f"📖 共 {total} 页，本次 OCR 第 {START_PAGE}~{end} 页")

    out = BASE / "book.txt"
    with open(out, "w", encoding="utf-8") as f:
        for i in range(START_PAGE - 1, end):
            pix = doc[i].get_pixmap(matrix=fitz.Matrix(DPI_ZOOM, DPI_ZOOM))
            img_bytes = pix.tobytes("png")
            text = ocr_image(img_bytes, token)
            f.write(f"--- 第 {i + 1} 页 ---\n")
            f.write(text + "\n\n")
            print(f"✅ 第 {i + 1}/{end} 页完成（{len(text)} 字）")
            time.sleep(0.3)  # 控制请求频率，避免触发 QPS 限制

    print(f"\n🎉 全部完成！文字已保存到: {out}")


if __name__ == "__main__":
    main()
