"""
client/cli.py — Wayfinder CLI

Wayfinder（寻路者）：可行动的智能行程寻路 Agent 命令行入口。
职责：装配 skills + TriggerFlow，流式打印 instant / 阶段事件。

运行方式（在项目根目录执行）：
  python -m client [用户需求...]
  python client/cli.py [用户需求...]
"""

import asyncio
import os
import sys
import tempfile
import warnings
from pathlib import Path
from typing import Any, cast

# 允许直接 python client/cli.py 运行（把项目根加入 sys.path）
_ROOT = str(Path(__file__).resolve().parent.parent)
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

warnings.filterwarnings("ignore")

from config import configure_agently
from agent_core.flows.travel_action_loop import build_travel_action_loop_flow
from skills import activate_travel_skills, create_travel_action_agent


def _print_stream_event(event: dict[str, Any]) -> None:
    phase = event.get("phase", "?")
    if phase == "plan_field":
        preview = str(event.get("value_preview", ""))[:60]
        print(f"  ↳ field {event['step']}.{event['path']} = {preview}")
    elif phase == "plan":
        reasoning = str(event.get("reasoning", ""))[:80]
        print(f"[Plan · Step {event['step']}] {event['decision']}: {reasoning}")
    elif phase == "execute":
        preview = str(event.get("result_preview", ""))[:80]
        print(f"[Execute] {event['tool']} → {preview}")


async def run(user_request: str, max_rounds: int = 15) -> None:
    workdir = tempfile.mkdtemp(prefix="travel_")
    action_agent = await create_travel_action_agent(workdir)
    active = activate_travel_skills(action_agent)

    print("=" * 64)
    print("Wayfinder — 可行动的智能行程寻路 Agent（v5 · instant + 流式输出）")
    print("=" * 64)
    print(f"已激活 {len(active)} 个工具（高德 {len(active) - 3} + 搜索/浏览 + bash）")
    print(f"工作目录：{workdir}\n")
    print(f"用户需求：{user_request}\n")
    print("─" * 64)
    print("[流式输出] instant 逐字段推送 + TriggerFlow 阶段事件：\n")

    flow = build_travel_action_loop_flow(max_rounds=max_rounds)
    execution = flow.create_execution(
        runtime_resources={
            "action_agent": action_agent,
            "user_request": user_request,
            "max_rounds": max_rounds,
        },
    )
    async for event in execution.get_async_runtime_stream(
        initial_value={"history": [], "step": 0},
        timeout=120,
    ):
        _print_stream_event(cast(dict[str, Any], event))

    result = execution._get_compat_result() or {}

    print("\n" + "─" * 64)
    answer = result.get("answer", "")
    if answer:
        print(f"\n[最终回答]\n{str(answer)[:600]}")

    plan_path = os.path.join(workdir, "plan.md")
    print(f"\n[产出文档] {plan_path} 存在：{os.path.exists(plan_path)}")
    if os.path.exists(plan_path):
        print("内容预览：")
        print(open(plan_path, encoding="utf-8").read()[:400])

    print("\n" + "=" * 64)
    print("关键观察：")
    print("  1. v4: async_put_into_stream 推送 TriggerFlow 阶段事件")
    print("  2. v5: get_async_generator(type='instant') 逐字段推送模型输出")
    print("  3. type/tool_name/tool_args 可以先被观察到")
    print("  4. 当前 demo 仍等字段流消费完成后再进入 Execute")
    print("  5. 两层流式叠加：字段级 + 阶段级，全链路可观测")
    print("=" * 64)


EXAMPLE_REQUESTS = (
    "帮我规划北京一日游",
    "帮我规划云南三日游",
    "帮我规划广州周末两日游，想吃早茶",
    "帮我规划成都三日游，含大熊猫基地",
)


def _prompt_user_request() -> str:
    print("样例输入（可直接复制）：")
    for index, example in enumerate(EXAMPLE_REQUESTS, start=1):
        print(f"  {index}、{example}")
    print()
    return input("请输入你的需求：").strip()


def main() -> None:
    configure_agently()
    if len(sys.argv) > 1:
        request = " ".join(sys.argv[1:])
    else:
        request = _prompt_user_request()
    asyncio.run(run(request))


if __name__ == "__main__":
    main()
