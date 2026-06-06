"""Function-calling 内置工具技能。"""

from skills.functionCalling.web_actions import WEB_ACTION_IDS, register_web_actions

__all__ = ["register_web_actions", "WEB_ACTION_IDS"]
