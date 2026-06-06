"""
旅游场景技能装配 — 组合 MCP / function-calling / bash

供 CLI 与 FastAPI 路由调用，与 TriggerFlow 编排层解耦。
"""

from agently import Agently

from skills.bash import BASH_SANDBOX_ID, register_bash_sandbox
from skills.functionCalling import WEB_ACTION_IDS, register_web_actions
from skills.mcp import list_map_skill_ids, register_amap_maps

TRAVEL_SYSTEM_PROMPT = (
    "你是旅游辅助助手。可以联网搜索攻略、用 browse 阅读网页、"
    "用高德地图查路线和距离、用 bash 把行程写成文档。"
    "先用工具查到真实信息，再给出可执行的行程，最后把行程写成 markdown 文件。"
)


async def register_travel_skills(agent, workdir: str) -> None:
    """向 agent 注册旅游场景所需的全部工具（不激活）。"""
    agent.set_agent_prompt("system", TRAVEL_SYSTEM_PROMPT)
    register_web_actions(agent)
    await register_amap_maps(agent)
    register_bash_sandbox(agent, workdir)


async def create_travel_action_agent(workdir: str):
    """创建并完成旅游工具注册的行动 agent。"""
    agent = Agently.create_agent()
    await register_travel_skills(agent, workdir)
    return agent


def activate_travel_skills(agent) -> list[str]:
    """激活地图 + 搜索 + 浏览 + bash，返回激活的 action id 列表。"""
    active = list_map_skill_ids(agent) + list(WEB_ACTION_IDS) + [BASH_SANDBOX_ID]
    agent.use_actions(active)
    return active
