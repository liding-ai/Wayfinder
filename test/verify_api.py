"""
test/verify_api.py — FastAPI 服务最小验收

用途：
  - 启动 Wayfinder 服务后运行，确认 /health 与 /v1/travel-agent/stream
  - 演示 HTTP + SSE 消费 instant 字段级流式输出

运行步骤：
  终端 A:  python -m agent_core.main
  终端 B:  python -m test.verify_api
"""

import json
import sys

import httpx

from config import SERVICE_URL

BASE_URL = SERVICE_URL


def check_health() -> None:
    print(f"GET {BASE_URL}/health")
    resp = httpx.get(f"{BASE_URL}/health", timeout=5)
    resp.raise_for_status()
    print(f"  → {resp.status_code} {resp.json()}")


def query_travel_agent_stream(request: str) -> None:
    print(f"\nPOST {BASE_URL}/v1/travel-agent/stream")
    print(f"  需求：{request}")
    with httpx.stream(
        "POST",
        f"{BASE_URL}/v1/travel-agent/stream",
        json={"request": request, "max_rounds": 5},
        timeout=120,
    ) as resp:
        resp.raise_for_status()
        for line in resp.iter_lines():
            if not line.startswith("data: "):
                continue
            event = json.loads(line[6:])
            phase = event.get("phase", "?")
            if phase == "plan_field":
                print(f"  ↳ field {event.get('step')}.{event.get('path')}")
            elif phase == "plan":
                print(f"  [Plan] {event.get('decision')}: {str(event.get('reasoning', ''))[:60]}")
            elif phase == "execute":
                print(f"  [Execute] {event.get('tool')}")
            elif phase == "done":
                print(f"  [Done] answer={str(event.get('answer', ''))[:80]}")
            elif phase == "error":
                print(f"  [Error] {event.get('detail')}")


def main() -> int:
    try:
        check_health()
    except httpx.ConnectError:
        print(f"连不上 {BASE_URL}，请先在另一终端运行: python -m agent_core.main")
        return 1

    try:
        query_travel_agent_stream("帮我规划北京一日游，写一份 plan.md")
    except httpx.HTTPStatusError as exc:
        print(f"  HTTP {exc.response.status_code} {exc.response.text}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
