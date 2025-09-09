from __future__ import annotations

import asyncio
import time
import uuid
from typing import Any, AsyncGenerator, Dict, List, Optional
import json

from fastapi import APIRouter, Form, HTTPException, Path
from fastapi.responses import StreamingResponse

from fathom.clients.azure_openai_client import (
    AzureOpenAIClient,
    load_azure_openai_config,
)


router = APIRouter()


@router.get("/status")
async def playground_status() -> Dict[str, str]:
    return {"status": "ok"}


@router.get("/agents")
async def list_agents() -> List[Dict[str, Any]]:
    # Single fixed agent for MVP, model label shown in UI from `provider`
    return [
        {
            "agent_id": "fathom-agent",
            "name": "Fathom",
            "description": "LUSID data-quality agent",
            "model": {
                "name": "GPT-4o (Azure)",
                "model": "gpt-4o",
                "provider": "gpt-4o",
            },
            "storage": False,
        }
    ]


@router.get("/teams")
async def list_teams() -> List[Dict[str, Any]]:
    # Single fixed team for MVP; UI defaults to team mode
    return [
        {
            "team_id": "fathom-team",
            "name": "Fathom Team",
            "description": "Fathom default team",
            "model": {
                "name": "GPT-4o (Azure)",
                "model": "gpt-4o",
                "provider": "gpt-4o",
            },
            "storage": False,
        }
    ]


def _now_epoch() -> int:
    return int(time.time())


async def _stream_run_from_azure(messages: List[Dict[str, Any]]) -> AsyncGenerator[bytes, None]:
    """Streams UI-compatible JSON event objects based on Azure OpenAI streaming."""
    # Resolve Azure OpenAI config
    cfg = load_azure_openai_config()
    client = AzureOpenAIClient(cfg)

    # Initialise run metadata
    run_id = str(uuid.uuid4())
    session_id = str(uuid.uuid4())
    created_at = _now_epoch()
    model_alias = "gpt-4o-azure"  # Alias; currently backed by gpt-4o deployment

    # Emit RunStarted
    start_obj = {
        "event": "RunStarted",
        "run_id": run_id,
        "session_id": session_id,
        "model": model_alias,
        "created_at": created_at,
    }
    yield json.dumps(start_obj).encode() + b"\n"

    accumulated = ""
    try:
        async for chunk in client.stream_chat(messages=messages, temperature=0.2):
            try:
                choices = chunk.get("choices", [])
                if not choices:
                    continue
                delta = choices[0].get("delta") or {}
                token = delta.get("content")
                if token:
                    accumulated += token
                    content_obj = {
                        "event": "RunResponseContent",
                        "content_type": "text/markdown",
                        "content": accumulated,
                        "model": model_alias,
                        "created_at": _now_epoch(),
                    }
                    yield json.dumps(content_obj).encode() + b"\n"
            except Exception:
                continue
    except Exception as e:
        err_obj = {
            "event": "RunError",
            "content_type": "text/plain",
            "content": f"{e}",
            "model": model_alias,
            "created_at": _now_epoch(),
        }
        yield json.dumps(err_obj).encode() + b"\n"
        return

    # Fallback: if no streamed tokens, attempt non-stream call once
    if not accumulated:
        try:
            resp = await client.chat(messages=messages, temperature=0.2)
            text = (
                (resp.get("choices") or [{}])[0]
                .get("message", {})
                .get("content", "")
            )
            if text:
                accumulated = text
                content_obj = {
                    "event": "RunResponseContent",
                    "content_type": "text/markdown",
                    "content": accumulated,
                    "model": model_alias,
                    "created_at": _now_epoch(),
                }
                yield json.dumps(content_obj).encode() + b"\n"
        except Exception as e:
            err_obj = {
                "event": "RunError",
                "content_type": "text/plain",
                "content": f"{e}",
                "model": model_alias,
                "created_at": _now_epoch(),
            }
            yield json.dumps(err_obj).encode() + b"\n"
            return

    # Emit RunCompleted
    end_obj = {
        "event": "RunCompleted",
        "content_type": "text/markdown",
        "content": accumulated,
        "model": model_alias,
        "created_at": _now_epoch(),
    }
    yield json.dumps(end_obj).encode() + b"\n"


@router.post("/agents/{agent_id}/runs")
async def run_agent(
    agent_id: str = Path(...),
    message: str = Form(...),
    stream: Optional[bool] = Form(default=True),
    session_id: Optional[str] = Form(default=None),
):
    if not message:
        raise HTTPException(status_code=400, detail="Missing message")

    messages = [{"role": "user", "content": message}]
    return StreamingResponse(
        _stream_run_from_azure(messages),
        media_type="application/json",
    )


@router.post("/teams/{team_id}/runs")
async def run_team(
    team_id: str = Path(...),
    message: str = Form(...),
    stream: Optional[bool] = Form(default=True),
    session_id: Optional[str] = Form(default=None),
):
    if not message:
        raise HTTPException(status_code=400, detail="Missing message")

    messages = [{"role": "user", "content": message}]
    return StreamingResponse(
        _stream_run_from_azure(messages),
        media_type="application/json",
    )


