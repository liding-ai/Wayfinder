"""项目配置：路径、环境变量、模型与服务端点。"""

from config.agently import configure_agently, make_agent
from config.service import SERVICE_HOST, SERVICE_PORT, SERVICE_URL
from config.settings import (
    PROJECT_ROOT,
    PROMPTS_DIR,
    get_amap_api_key,
    get_env,
    load_env,
    require_env,
)

__all__ = [
    "PROJECT_ROOT",
    "PROMPTS_DIR",
    "SERVICE_HOST",
    "SERVICE_PORT",
    "SERVICE_URL",
    "configure_agently",
    "make_agent",
    "get_env",
    "require_env",
    "get_amap_api_key",
    "load_env",
]
