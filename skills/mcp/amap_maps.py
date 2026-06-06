"""
高德地图 MCP — 地理编码、路线规划等地图能力

通过 MCP 协议接入 mcp.amap.com，将地图工具注册到 agent。
"""

from config.settings import get_amap_api_key


def build_amap_mcp_url() -> str:
    return f"https://mcp.amap.com/mcp?key={get_amap_api_key()}"


async def register_amap_maps(agent) -> None:
    """注册高德地图 MCP 工具集。"""
    await agent.async_use_mcp(build_amap_mcp_url())


def list_map_skill_ids(agent) -> list[str]:
    """返回已注册的地图类 action id（名称含 map）。"""
    all_ids = agent.action.action_registry.list_action_ids()
    return [action_id for action_id in all_ids if "map" in action_id.lower()]
