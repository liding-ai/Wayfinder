"""
agent_core/flows/travel_action_loop.py — Reason / Act 循环编排

职责：
  - reason / act 是模块顶层 chunk，便于测试与复用
  - build_travel_action_loop_flow() 装配 TriggerFlow 与默认 runtime_resources
  - action_agent、user_request 等请求级依赖通过 runtime_resources 注入

v5 特性：
  - reason 阶段用 get_async_generator(type="instant") 逐字段消费模型输出
  - async_put_into_stream 推送 plan_field / plan / execute 阶段事件
  - 字段流消费完成后再进入 Execute（提前执行需额外调度逻辑）
"""

from pathlib import Path
from typing import Any, Callable, cast

from agently import Agent, TriggerFlow, TriggerFlowRuntimeData

from config import PROMPTS_DIR, make_agent


async def reason(data: TriggerFlowRuntimeData) -> None:
    state = data.input if isinstance(data.input, dict) else {}
    step = state.get("step", 0) + 1
    history = state.get("history", [])

    user_request = cast(str, data.require_resource("user_request"))
    action_agent = cast(Agent, data.require_resource("action_agent"))
    max_rounds = int(data.require_resource("max_rounds"))
    agent_factory = cast(Callable[[], Agent], data.require_resource("agent_factory"))
    prompts_path = cast(Path, data.require_resource("prompts_path"))

    tools_desc = [
        {"name": t["name"], "desc": t["desc"], "args": t.get("kwargs", {})}
        for t in action_agent.action.get_tool_list()
    ]

    response = (
        agent_factory()
        .load_yaml_prompt(
            prompts_path,
            prompt_key_path="reason_decision",
            mappings={
                "user_request": user_request,
                "step": step,
                "max_rounds": max_rounds,
            },
        )
        .info({"可用工具": tools_desc, "已执行步骤": history})
        .get_response()
    )

    decision: dict[str, Any] = {}
    async for streaming_data in response.get_async_generator(type="instant"):
        if streaming_data.event_type == "done":
            path = streaming_data.path
            value = streaming_data.value
            decision[path] = value
            await data.async_put_into_stream(
                {
                    "phase": "plan_field",
                    "step": step,
                    "path": path,
                    "value_preview": str(value)[:100],
                }
            )

    final = await response.async_get_data()
    for key, value in final.items():
        if key not in decision:
            decision[key] = value

    await data.async_put_into_stream(
        {
            "phase": "plan",
            "step": step,
            "reasoning": str(decision.get("reasoning", "")),
            "decision": str(decision.get("type", "")),
        }
    )

    state["step"] = step
    if decision.get("type") == "final":
        await data.async_set_state("answer", str(decision.get("answer", "")))
        return
    if step >= max_rounds:
        await data.async_set_state("answer", "达到最大轮数限制")
        return
    if decision.get("type") == "tool" and decision.get("tool_name"):
        state["action_calls"] = [
            {
                "name": str(decision["tool_name"]),
                "kwargs": decision.get("tool_args") or {},
            }
        ]
        await data.async_emit_nowait("Act", state)
    else:
        await data.async_set_state("answer", "模型未给出有效的工具调用或最终回答")


async def act(data: TriggerFlowRuntimeData) -> None:
    state = data.input if isinstance(data.input, dict) else {}
    action_agent = cast(Agent, data.require_resource("action_agent"))

    results = []
    for call in state.pop("action_calls", []):
        name, kwargs = call["name"], call["kwargs"]
        try:
            result = await action_agent.action.async_execute_action(name, kwargs)
        except Exception as exc:
            result = {"ok": False, "error": str(exc)}
        results.append({"tool": name, "args": kwargs, "result": result})
        await data.async_put_into_stream(
            {
                "phase": "execute",
                "tool": name,
                "result_preview": str(result)[:120],
            }
        )

    history = state.get("history", [])
    history.extend(results)
    state["history"] = history
    await data.async_emit_nowait("Reason", state)


def build_travel_action_loop_flow(
    *,
    agent_factory: Callable[[], Agent] = make_agent,
    prompts_path: Path = PROMPTS_DIR / "travel_reason_decision.yaml",
    max_rounds: int = 15,
) -> TriggerFlow:
    flow = TriggerFlow(name="travel-action-loop")
    flow.update_runtime_resources(
        agent_factory=agent_factory,
        prompts_path=prompts_path,
        max_rounds=max_rounds,
    )

    flow.to(reason)
    flow.when("Act").to(act)
    flow.when("Reason").to(reason)

    return flow
