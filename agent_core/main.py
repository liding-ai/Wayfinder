"""
agent_core/main.py — 服务入口

启动顺序：
  1. configure_agently() —— 注入模型配置
  2. 创建 FastAPI app，注册路由
  3. uvicorn 接管 HTTP 请求

启动方式（在项目根目录执行）：
  python -m agent_core.main
  或
  uvicorn agent_core.main:app --host 0.0.0.0 --port 8000 --reload
"""

import sys
from pathlib import Path

# 允许直接 python agent_core/main.py 运行（把项目根加入 sys.path）
_ROOT = str(Path(__file__).resolve().parent.parent)
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from fastapi import FastAPI

from config import SERVICE_HOST, SERVICE_PORT, configure_agently
from agent_core.routers.travel_api import router as travel_api_router

configure_agently()

app = FastAPI(
    title="Wayfinder",
    description="Wayfinder — 可行动的智能行程寻路 Agent（v5 · instant 流式 + FastAPI 服务化）",
    version="0.1.0",
)


@app.get("/health", tags=["system"])
def health_check():
    """部署时供探活使用。"""
    return {"status": "ok", "service": "wayfinder", "version": app.version}


app.include_router(travel_api_router, prefix="/v1")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "agent_core.main:app",
        host=SERVICE_HOST,
        port=SERVICE_PORT,
        reload=False,
    )
