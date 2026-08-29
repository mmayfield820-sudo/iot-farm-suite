from __future__ import annotations

import argparse
import json
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen


def ask(question: str, session_id: str, plot_id: str | None) -> None:
    body = {"message": question}
    if plot_id:
        body["plotId"] = plot_id
    request = Request(
        f"http://127.0.0.1:8000/chat/sessions/{quote(session_id, safe='')}/messages",
        data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    try:
        with urlopen(request, timeout=120) as response:
            result = json.loads(response.read().decode("utf-8"))
    except HTTPError as error:
        print(f"请求失败：HTTP {error.code}")
        return
    except (URLError, TimeoutError, OSError) as error:
        print(f"无法连接 AI 服务：{type(error).__name__}")
        return
    print(result.get("answer") or "回答为空")
    if result.get("sources"):
        print("\n参考来源：")
        for source in result["sources"]:
            print(f"- {source}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="测试当前 AI 服务接口")
    parser.add_argument("question", nargs="+", help="要询问的问题")
    parser.add_argument("--session", default="test", help="会话 ID")
    parser.add_argument("--plot", help="可选地块 ID；直接调用 AI 时不会自动查询数据库")
    arguments = parser.parse_args()
    ask(" ".join(arguments.question), arguments.session, arguments.plot)
