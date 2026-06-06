"""
联网 function-calling — Search / Browse

通过 agently builtins 将搜索与网页浏览注册为 agent 可调用的 action。
"""

from agently.builtins.actions import Browse, Search

WEB_ACTION_IDS = ("search", "browse")


def register_web_actions(agent) -> None:
    """注册 search、browse 工具。"""
    Search().register_actions(agent.action)
    Browse().register_actions(agent.action)
