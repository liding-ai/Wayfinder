"""Agently 全局模型配置与 agent 工厂。"""

from agently import Agently

from config.settings import get_env


def configure_agently() -> None:
    """启动时调用一次：把模型配置注入 Agently。多次调用是幂等的。"""
    Agently.set_settings(
        "OpenAICompatible",
        {
            "base_url": get_env("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
            "model": get_env("DEEPSEEK_DEFAULT_MODEL", "deepseek-chat"),
            "auth": get_env("DEEPSEEK_API_KEY", ""),
        },
    )


def make_agent():
    """返回无工具的新 Agently agent 实例（供规划 LLM 使用）。"""
    return Agently.create_agent()
