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
from fathom.tools.registry import get_tool_definitions, execute_tool_call, build_tool_cheat_sheet
import lusid


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
    # Initialise run metadata early so we can emit a clean error if config is missing
    run_id = str(uuid.uuid4())
    session_id = str(uuid.uuid4())
    created_at = _now_epoch()
    model_alias = "gpt-4o-azure"  # Alias; currently backed by gpt-4o deployment

    # Emit RunStarted immediately
    start_obj = {
        "event": "RunStarted",
        "run_id": run_id,
        "session_id": session_id,
        "model": model_alias,
        "created_at": created_at,
    }
    yield json.dumps(start_obj).encode() + b"\n"

    # Resolve Azure OpenAI config; if missing, emit RunError and exit gracefully
    try:
        cfg = load_azure_openai_config()
        client = AzureOpenAIClient(cfg)
    except Exception as e:
        err_obj = {
            "event": "RunError",
            "content_type": "text/plain",
            "content": f"Azure OpenAI configuration error: {e}",
            "model": model_alias,
            "created_at": _now_epoch(),
        }
        yield json.dumps(err_obj).encode() + b"\n"
        return

    # Prepare tool registry and hidden system context
    tools = get_tool_definitions()
    cheat_sheet = build_tool_cheat_sheet()
    system_msg = {"role": "system", "content": cheat_sheet}
    convo: List[Dict[str, Any]] = [system_msg] + messages

    accumulated = ""
    try:
        async for chunk in client.stream_chat(messages=convo, temperature=0.2, tools=tools, tool_choice="auto"):
            try:
                choices = chunk.get("choices", [])
                if not choices:
                    continue
                delta = choices[0].get("delta") or {}

                # Tool calls in stream (Azure style) can appear as tool_calls list on message
                tool_calls = delta.get("tool_calls") or []
                if tool_calls:
                    # For each tool call, execute synchronously and push tool message into convo; then continue
                    for call in tool_calls:
                        tool_call_id = call.get("id") or str(uuid.uuid4())
                        fn = (call.get("function") or {})
                        name = fn.get("name")
                        raw_args = fn.get("arguments") or "{}"
                        try:
                            args = json.loads(raw_args) if isinstance(raw_args, str) else (raw_args or {})
                        except Exception:
                            args = {}

                        # Emit tool start
                        start_evt = {
                            "event": "RunToolCallStarted",
                            "tool_name": name,
                            "tool_call_id": tool_call_id,
                            "created_at": _now_epoch(),
                        }
                        yield json.dumps(start_evt).encode() + b"\n"

                        # Execute tool
                        from main import app
                        api_factory: lusid.ApiClientFactory | None = getattr(app.state, "lusid_factory", None)
                        try:
                            result = execute_tool_call(api_factory, name=name, arguments=args)
                            tool_msg = {
                                "role": "tool",
                                "tool_call_id": tool_call_id,
                                "name": name,
                                "content": json.dumps(result),
                            }
                            convo.append(tool_msg)

                            # Emit tool completed with compact content
                            done_evt = {
                                "event": "RunToolCallCompleted",
                                "tool_name": name,
                                "tool_call_id": tool_call_id,
                                "created_at": _now_epoch(),
                                "content": result,
                            }
                            yield json.dumps(done_evt).encode() + b"\n"
                        except Exception as te:
                            err_payload = {"error": str(te)}
                            tool_msg = {
                                "role": "tool",
                                "tool_call_id": tool_call_id,
                                "name": name,
                                "content": json.dumps(err_payload),
                            }
                            convo.append(tool_msg)
                            err_evt = {
                                "event": "RunToolCallCompleted",
                                "tool_name": name,
                                "tool_call_id": tool_call_id,
                                "created_at": _now_epoch(),
                                "content": err_payload,
                            }
                            yield json.dumps(err_evt).encode() + b"\n"

                    # After handling tool calls, immediately trigger a non-stream assistant turn to integrate tool results
                    try:
                        follow = await client.chat(messages=convo, temperature=0.2, tools=tools, tool_choice="auto")
                        text = ((follow.get("choices") or [{}])[0].get("message", {}) or {}).get("content")
                        if text:
                            accumulated += text
                            content_obj = {
                                "event": "RunResponseContent",
                                "content_type": "text/markdown",
                                "content": accumulated,
                                "model": model_alias,
                                "created_at": _now_epoch(),
                            }
                            yield json.dumps(content_obj).encode() + b"\n"
                        break
                    except Exception:
                        # If follow-up fails, continue streaming loop
                        continue

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
            resp = await client.chat(messages=convo, temperature=0.2, tools=tools, tool_choice="auto")
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


