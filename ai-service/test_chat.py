# -*- coding: utf-8 -*-
"""
调试脚本：直接跑，输入问题看答案，不用开浏览器。
同一段对话（同一个 session_id）会记住之前问过什么，能回答"那…呢"这种指代问题。
用法：
    python test_chat.py                  # 交互模式，一直问，输入 q 退出
    python test_chat.py 黄瓜怎么浇水       # 直接问一个问题（单轮）
    python test_chat.py --sid 对话A        # 指定会话编号（测试多轮对话用）
"""
import sys

import requests

# Windows 控制台中文显示
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

URL = "http://127.0.0.1:8000/chat"
SESSION_ID = "test"   # 同一个 session 算一段对话
USER_ID = "default"   # 用户标识：档案/记忆按它隔离


def ask(q: str, session_id: str = SESSION_ID, user_id: str = USER_ID):
    print("（大模型思考中，通常 5~30 秒，请稍等……）")
    try:
        r = requests.post(URL, json={"question": q, "session_id": session_id, "user_id": user_id}, timeout=120)
    except Exception as e:
        print(f"[出错了] 连不上 {URL}：{type(e).__name__}")
        print("（先确认服务已经启动：python app.py）")
        print("（如果 8000 被旧进程占用，先在旧终端按 Ctrl+C，再重新 python app.py）")
        return
    if r.status_code != 200:
        print(f"[出错了] 状态码 {r.status_code}：{r.text}")
        return
    data = r.json()
    if "error" in data:
        print(f"[服务端报错] {data['error']}")
        return
    print("=" * 60)
    print(f"[会话 {session_id} | 用户 {user_id}] 回答：")
    print(data.get("answer") or "（回答为空）")
    print("-" * 60)
    print("本次实际用到的资料（证明是检索/搜索来的，不是瞎编）：")
    for ref in data.get("refs", []):
        tag = "知识库" if "农业知识库" in ref["source"] else "联网搜索"
        print(f"  [{tag}·{ref['source']}] {ref['text'][:70]}...")
    if not data.get("refs"):
        print("  （这次没用到资料，可能是寒暄/闲聊）")
    print()


if __name__ == "__main__":
    args = sys.argv[1:]
    session_id = SESSION_ID
    user_id = USER_ID
    if "--sid" in args:
        i = args.index("--sid")
        if i + 1 < len(args):
            session_id = args[i + 1]
            args = args[:i] + args[i + 2:]
    if "--uid" in args:
        i = args.index("--uid")
        if i + 1 < len(args):
            user_id = args[i + 1]
            args = args[:i] + args[i + 2:]

    if args:
        ask(" ".join(args), session_id, user_id)
    else:
        print("先确保服务已启动（python app.py）")
        print(f"当前会话：{session_id} | 用户：{user_id}（另开会话加 --sid，换用户加 --uid 名字）")
        print("输入问题回车，输入 q 退出。\n")
        while True:
            q = input("你的问题：").strip()
            if q.lower() == "q":
                break
            if q:
                ask(q, session_id, user_id)
