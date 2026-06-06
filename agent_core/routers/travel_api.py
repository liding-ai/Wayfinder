"""
agent_core/routers/travel_api.py — Wayfinder HTTP 接入层

职责（route handler 三件事）：
  1. 解开 HTTP 请求体（Pydantic 校验）
  2. 调用业务层（flow.create_execution + runtime stream）
  3. 把结果包装成 HTTP 响应（JSON 或 SSE）
"""

import json
import os
import tempfile
from collections.abc import AsyncIterator
from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from agent_core.flows.travel_action_loop import build_travel_action_loop_flow
from skills import activate_travel_skills, create_travel_action_agent

_flow = build_travel_action_loop_flow()

router = APIRouter(tags=["travel-agent"])


class TravelPlanRequest(BaseModel):
    request: str = Field(..., min_length=1, description="用户的旅游规划需求")
    max_rounds: int = Field(15, ge=1, le=30, description="action loop 最大轮数")


class TravelPlanResponse(BaseModel):
    answer: str = Field(..., description="最终回答")
    workdir: str = Field(..., description="bash sandbox 工作目录（plan.md 可能在此）")
    plan_exists: bool = Field(..., description="workdir/plan.md 是否已生成")


async def _prepare_execution(req: TravelPlanRequest) -> tuple[Any, str]:
    workdir = tempfile.mkdtemp(prefix="travel_")
    try:
        action_agent = await create_travel_action_agent(workdir)
    except KeyError as exc:
        raise HTTPException(
            status_code=500,
            detail="missing required env var: AMAP_API_KEY",
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"failed to build travel agent: {exc}",
        ) from exc

    activate_travel_skills(action_agent)
    execution = _flow.create_execution(
        runtime_resources={
            "action_agent": action_agent,
            "user_request": req.request,
            "max_rounds": req.max_rounds,
        },
    )
    return execution, workdir


@router.post("/travel-agent", response_model=TravelPlanResponse)
async def create_travel_plan(req: TravelPlanRequest) -> TravelPlanResponse:
    execution, workdir = await _prepare_execution(req)

    try:
        async for _event in execution.get_async_runtime_stream(
            initial_value={"history": [], "step": 0},
            timeout=120,
        ):
            pass
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"flow execution failed: {exc}") from exc

    result = execution._get_compat_result() or {}
    plan_path = os.path.join(workdir, "plan.md")
    return TravelPlanResponse(
        answer=str(result.get("answer", "")),
        workdir=workdir,
        plan_exists=os.path.exists(plan_path),
    )


@router.post("/travel-agent/stream")
async def stream_travel_plan(req: TravelPlanRequest) -> StreamingResponse:
    execution, workdir = await _prepare_execution(req)

    async def event_generator() -> AsyncIterator[str]:
        try:
            async for event in execution.get_async_runtime_stream(
                initial_value={"history": [], "step": 0},
                timeout=120,
            ):
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"

            result = execution._get_compat_result() or {}
            plan_path = os.path.join(workdir, "plan.md")
            done_event = {
                "phase": "done",
                "answer": str(result.get("answer", "")),
                "workdir": workdir,
                "plan_exists": os.path.exists(plan_path),
            }
            yield f"data: {json.dumps(done_event, ensure_ascii=False)}\n\n"
        except Exception as exc:
            yield f"data: {json.dumps({'phase': 'error', 'detail': str(exc)}, ensure_ascii=False)}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
