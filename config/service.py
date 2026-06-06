"""FastAPI / 验收脚本等服务端点配置。"""

from config.settings import get_env

SERVICE_HOST = get_env("SERVICE_HOST", "127.0.0.1") or "127.0.0.1"
SERVICE_PORT = int(get_env("SERVICE_PORT", "8000") or "8000")
SERVICE_URL = get_env("SERVICE_URL", f"http://{SERVICE_HOST}:{SERVICE_PORT}") or (
    f"http://{SERVICE_HOST}:{SERVICE_PORT}"
)
