from __future__ import annotations

import asyncio
import time
import uuid
from typing import Any, AsyncGenerator, Dict, List, Optional, Tuple
import json

from fastapi import APIRouter, Form, HTTPException, Path
from fastapi.responses import StreamingResponse, JSONResponse

from fathom.clients.azure_openai_client import (
    AzureOpenAIClient,
    load_azure_openai_config,
)
from fathom.tools.registry import get_tool_definitions, execute_tool_call, build_tool_cheat_sheet
from fathom.tools.compact import build_prompt_context
import lusid
from fathom.storage.azure_storage import AzureStorage
try:
    import tiktoken  # type: ignore
except Exception:
    tiktoken = None


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
            "storage": True,
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
def _approx_token_count(model: str, messages: List[Dict[str, Any]]) -> int:
    """Accurately count tokens when possible using tiktoken; fall back to rough char/4.

    Counts tokens for the prompt (system + transcript + current user turn). Assumes OpenAI-like chat format.
    """
    # Combine content fields only (tool messages include JSON strings)
    text_parts: List[str] = []
    for m in messages:
        role = m.get("role") or ""
        if role == "assistant" and m.get("tool_calls"):
            # tool_calls: count function name + arguments roughly
            for tc in (m.get("tool_calls") or []):
                fn = (tc or {}).get("function") or {}
                name = fn.get("name") or ""
                args = fn.get("arguments") or ""
                text_parts.append(name)
                if isinstance(args, str):
                    text_parts.append(args)
                else:
                    try:
                        text_parts.append(json.dumps(args))
                    except Exception:
                        pass
        content = m.get("content")
        if content is None:
            continue
        if isinstance(content, str):
            text_parts.append(content)
        else:
            # Non-string content (e.g., structured) → stringify
            try:
                text_parts.append(json.dumps(content))
            except Exception:
                pass

    combined = "\n".join(text_parts)
    if tiktoken is not None:
        try:
            # Use GPT-4o encoding as a proxy
            enc = tiktoken.get_encoding("o200k_base")
            return len(enc.encode(combined))
        except Exception:
            pass
    # Fallback heuristic
    return max(1, (len(combined) // 4))


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
        # Stream with mid-turn tool-call support (up to 4 iterations)
        iterations = 0
        while iterations < 4:
            iterations += 1
            pending_calls: Dict[int, Dict[str, Any]] = {}
            # Stream one assistant turn
            async for chunk in client.stream_chat(messages=convo, temperature=0.2, tools=tools, tool_choice="auto"):
                try:
                    choices = chunk.get("choices", [])
                    if not choices:
                        continue
                    delta = choices[0].get("delta") or {}
                    finish_reason = choices[0].get("finish_reason")

                    # Accumulate tool_call parts by index
                    stream_calls = delta.get("tool_calls") or []
                    for call in stream_calls:
                        idx = call.get("index", 0)
                        existing = pending_calls.get(idx) or {"id": call.get("id") or str(uuid.uuid4()), "name": None, "arguments": ""}
                        fn = call.get("function") or {}
                        if fn.get("name"):
                            existing["name"] = fn.get("name")
                        if "arguments" in fn and fn.get("arguments"):
                            existing["arguments"] += fn.get("arguments")
                        pending_calls[idx] = existing

                    token = delta.get("content")
                    if token:
                        accumulated += token
                        yield json.dumps({
                            "event": "RunResponseContent",
                            "content_type": "text/markdown",
                            "content": accumulated,
                            "model": model_alias,
                            "created_at": _now_epoch(),
                        }).encode() + b"\n"

                    if finish_reason == "tool_calls":
                        break
                except Exception:
                    continue

            # If no tool calls requested during stream, we're done
            if not pending_calls:
                break

            # Execute the pending tool calls, append results, then loop to stream again
            assistant_tool_calls = []
            for idx in sorted(pending_calls.keys()):
                c = pending_calls[idx]
                assistant_tool_calls.append({
                    "id": c["id"],
                    "type": "function",
                    "function": {"name": c.get("name") or "", "arguments": c.get("arguments") or "{}"},
                })
            convo.append({"role": "assistant", "tool_calls": assistant_tool_calls})

            from main import app
            api_factory: lusid.ApiClientFactory | None = getattr(app.state, "lusid_factory", None)
            for c in assistant_tool_calls:
                tool_call_id = c.get("id") or str(uuid.uuid4())
                name = (c.get("function") or {}).get("name")
                raw_args = (c.get("function") or {}).get("arguments") or "{}"
                try:
                    args = json.loads(raw_args) if isinstance(raw_args, str) else (raw_args or {})
                except Exception:
                    args = {}

                start_evt = {
                    "event": "ToolCallStarted",
                    "tool_name": name,
                    "tool_call_id": tool_call_id,
                    "created_at": _now_epoch(),
                    "tool": {
                        "role": "assistant",
                        "content": None,
                        "tool_call_id": tool_call_id,
                        "tool_name": name,
                        "tool_args": {k: str(v) for k, v in (args or {}).items()},
                        "tool_call_error": False,
                        "metrics": {"time": 0},
                        "created_at": _now_epoch(),
                    },
                }
                yield json.dumps(start_evt).encode() + b"\n"

                try:
                    t0 = time.time()
                    result = execute_tool_call(api_factory, name=name, arguments=args)
                    elapsed = int((time.time() - t0) * 1000)
                    tool_msg = {"role": "tool", "tool_call_id": tool_call_id, "name": name, "content": json.dumps(result)}
                    convo.append(tool_msg)
                    done_evt = {
                        "event": "ToolCallCompleted",
                        "tool_name": name,
                        "tool_call_id": tool_call_id,
                        "created_at": _now_epoch(),
                        "content": result,
                        "tool": {
                            "role": "tool",
                            "content": json.dumps(result),
                            "tool_call_id": tool_call_id,
                            "tool_name": name,
                            "tool_args": {k: str(v) for k, v in (args or {}).items()},
                            "tool_call_error": False,
                            "metrics": {"time": elapsed},
                            "created_at": _now_epoch(),
                        },
                    }
                    yield json.dumps(done_evt).encode() + b"\n"
                except Exception as te:
                    err_payload = {"error": str(te)}
                    tool_msg = {"role": "tool", "tool_call_id": tool_call_id, "name": name, "content": json.dumps(err_payload)}
                    convo.append(tool_msg)
                    err_evt = {
                        "event": "ToolCallCompleted",
                        "tool_name": name,
                        "tool_call_id": tool_call_id,
                        "created_at": _now_epoch(),
                        "content": err_payload,
                        "tool": {
                            "role": "tool",
                            "content": json.dumps(err_payload),
                            "tool_call_id": tool_call_id,
                            "tool_name": name,
                            "tool_args": {k: str(v) for k, v in (args or {}).items()},
                            "tool_call_error": True,
                            "metrics": {"time": 0},
                            "created_at": _now_epoch(),
                        },
                    }
                    yield json.dumps(err_evt).encode() + b"\n"
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


def _compact_transcript_for_prompt(messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Return a compacted transcript that prefers compact tool messages if present.

    When both full and compact exist for the same tool_call_id, keep only the compact one.
    """
    compact_by_id: Dict[str, Dict[str, Any]] = {}
    for m in messages:
        if m.get("role") == "tool" and m.get("is_compact") and m.get("tool_call_id"):
            compact_by_id[str(m.get("tool_call_id"))] = m

    out: List[Dict[str, Any]] = []
    for m in messages:
        if m.get("role") == "tool":
            tcid = str(m.get("tool_call_id") or "")
            if tcid and tcid in compact_by_id:
                # Skip non-compact duplicates; compact version will be emitted in its turn
                if not m.get("is_compact"):
                    continue
                # For compact, include as a plain tool message (drop the marker)
                compact = dict(m)
                compact.pop("is_compact", None)
                out.append(compact)
            else:
                out.append(m)
        else:
            out.append(m)
    return out


async def _stream_run_with_storage(
    prompt_history_and_user: List[Dict[str, Any]],
    session_id: str,
    storage: AzureStorage,
) -> AsyncGenerator[bytes, None]:
    """Stream a run using full prior transcript + current user message and persist the new turn.

    Persists, in order for this turn:
    - user message
    - assistant tool_calls (if any)
    - tool result messages (for each tool call)
    - assistant final message
    """
    run_id = str(uuid.uuid4())
    created_at = _now_epoch()
    model_alias = "gpt-4o-azure"

    # Emit RunStarted immediately with provided session_id and token count
    start_obj = {
        "event": "RunStarted",
        "run_id": run_id,
        "session_id": session_id,
        "model": model_alias,
        "created_at": created_at,
    }
    # Compute token count for system + transcript + current user
    try:
        tools = get_tool_definitions()
        cheat_sheet = build_tool_cheat_sheet()
        system_msg = {"role": "system", "content": cheat_sheet}
        prompt_messages = [system_msg] + prior_and_current_messages
        start_obj["extra_data"] = {"token_count": _approx_token_count(model_alias, prompt_messages)}
    except Exception:
        pass
    yield json.dumps(start_obj).encode() + b"\n"

    # Resolve Azure OpenAI config
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
    convo: List[Dict[str, Any]] = [system_msg] + prompt_history_and_user

    # Prepare persistence for this turn
    persist_messages: List[Dict[str, Any]] = []
    if prompt_history_and_user:
        last_msg = prompt_history_and_user[-1]
        if last_msg.get("role") == "user":
            # Ensure a timestamp exists
            if "created_at" not in last_msg:
                last_msg = {**last_msg, "created_at": _now_epoch()}
                # Replace in convo as well
                convo[-1] = last_msg
            persist_messages.append(last_msg)

    accumulated = ""
    try:
        iterations = 0
        while iterations < 4:
            iterations += 1
            pending_calls: Dict[int, Dict[str, Any]] = {}
            # Stream one assistant turn
            async for chunk in client.stream_chat(messages=convo, temperature=0.2, tools=tools, tool_choice="auto"):
                try:
                    choices = chunk.get("choices", [])
                    if not choices:
                        continue
                    delta = choices[0].get("delta") or {}
                    finish_reason = choices[0].get("finish_reason")

                    # Accumulate tool_call parts by index
                    stream_calls = delta.get("tool_calls") or []
                    for call in stream_calls:
                        idx = call.get("index", 0)
                        existing = pending_calls.get(idx) or {"id": call.get("id") or str(uuid.uuid4()), "name": None, "arguments": ""}
                        fn = call.get("function") or {}
                        if fn.get("name"):
                            existing["name"] = fn.get("name")
                        if "arguments" in fn and fn.get("arguments"):
                            existing["arguments"] += fn.get("arguments")
                        pending_calls[idx] = existing

                    token = delta.get("content")
                    if token:
                        accumulated += token
                        yield json.dumps({
                            "event": "RunResponseContent",
                            "content_type": "text/markdown",
                            "content": accumulated,
                            "model": model_alias,
                            "created_at": _now_epoch(),
                        }).encode() + b"\n"

                    if finish_reason == "tool_calls":
                        break
                except Exception:
                    continue

            # If no tool calls requested during stream, we're done
            if not pending_calls:
                break

            # Persist assistant tool_calls as a message for this turn
            assistant_tool_calls = []
            for idx in sorted(pending_calls.keys()):
                c = pending_calls[idx]
                assistant_tool_calls.append({
                    "id": c["id"],
                    "type": "function",
                    "function": {"name": c.get("name") or "", "arguments": c.get("arguments") or "{}"},
                })
            tool_calls_msg = {
                "role": "assistant",
                "content": None,
                "tool_calls": assistant_tool_calls,
                "created_at": _now_epoch(),
            }
            persist_messages.append(tool_calls_msg)
            convo.append(tool_calls_msg)

            # Execute the pending tool calls, append results, then loop to stream again
            from main import app
            api_factory: lusid.ApiClientFactory | None = getattr(app.state, "lusid_factory", None)
            for c in assistant_tool_calls:
                tool_call_id = c.get("id") or str(uuid.uuid4())
                name = (c.get("function") or {}).get("name")
                raw_args = (c.get("function") or {}).get("arguments") or "{}"
                try:
                    args = json.loads(raw_args) if isinstance(raw_args, str) else (raw_args or {})
                except Exception:
                    args = {}

                start_evt = {
                    "event": "ToolCallStarted",
                    "tool_name": name,
                    "tool_call_id": tool_call_id,
                    "created_at": _now_epoch(),
                    "tool": {
                        "role": "assistant",
                        "content": None,
                        "tool_call_id": tool_call_id,
                        "tool_name": name,
                        "tool_args": {k: str(v) for k, v in (args or {}).items()},
                        "tool_call_error": False,
                        "metrics": {"time": 0},
                        "created_at": _now_epoch(),
                    },
                }
                yield json.dumps(start_evt).encode() + b"\n"

                try:
                    t0 = time.time()
                    result = execute_tool_call(api_factory, name=name, arguments=args)
                    elapsed = int((time.time() - t0) * 1000)
                    # Persist full result for UI/history (do not add to convo)
                    tool_msg = {"role": "tool", "tool_call_id": tool_call_id, "name": name, "content": json.dumps(result), "created_at": _now_epoch()}
                    persist_messages.append(tool_msg)
                    # Build compact prompt context for the model and stage it as a compact tool message
                    compact_text = build_prompt_context(name, result, args)
                    convo.append({"role": "tool", "tool_call_id": tool_call_id, "name": name, "content": compact_text, "is_compact": True})
                    done_evt = {
                        "event": "ToolCallCompleted",
                        "tool_name": name,
                        "tool_call_id": tool_call_id,
                        "created_at": _now_epoch(),
                        "content": result,
                        "tool": {
                            "role": "tool",
                            "content": json.dumps(result),
                            "tool_call_id": tool_call_id,
                            "tool_name": name,
                            "tool_args": {k: str(v) for k, v in (args or {}).items()},
                            "tool_call_error": False,
                            "metrics": {"time": elapsed},
                            "created_at": _now_epoch(),
                            "compact_context": compact_text,
                        },
                    }
                    yield json.dumps(done_evt).encode() + b"\n"
                except Exception as te:
                    err_payload = {"error": str(te)}
                    tool_msg = {"role": "tool", "tool_call_id": tool_call_id, "name": name, "content": json.dumps(err_payload), "created_at": _now_epoch()}
                    convo.append(tool_msg)
                    persist_messages.append(tool_msg)
                    err_evt = {
                        "event": "ToolCallCompleted",
                        "tool_name": name,
                        "tool_call_id": tool_call_id,
                        "created_at": _now_epoch(),
                        "content": err_payload,
                        "tool": {
                            "role": "tool",
                            "content": json.dumps(err_payload),
                            "tool_call_id": tool_call_id,
                            "tool_name": name,
                            "tool_args": {k: str(v) for k, v in (args or {}).items()},
                            "tool_call_error": True,
                            "metrics": {"time": 0},
                            "created_at": _now_epoch(),
                        },
                    }
                    yield json.dumps(err_evt).encode() + b"\n"
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

    # Persist final assistant message for this turn
    final_assistant = {
        "role": "assistant",
        "content": accumulated,
        "created_at": _now_epoch(),
    }
    persist_messages.append(final_assistant)

    try:
        storage.append_messages(session_id=session_id, new_messages=persist_messages)
        storage.touch_session(session_id=session_id, increment_messages_by=len(persist_messages))
    except Exception:
        # Best-effort persistence; do not fail the stream
        pass

    # Build compacted transcript for token count and final prompt reflection
    compact_convo = [system_msg] + _compact_transcript_for_prompt(prompt_history_and_user)
    # Emit RunCompleted (also include token count as final confirmation)
    end_obj = {
        "event": "RunCompleted",
        "content_type": "text/markdown",
        "content": accumulated,
        "model": model_alias,
        "created_at": _now_epoch(),
        "extra_data": {
            "token_count": _approx_token_count(model_alias, compact_convo)
        }
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
    # Resolve storage and session
    storage = AzureStorage()
    # Title from first message
    # Sanitize incoming session_id: treat '', 'null', 'undefined' as empty
    sanitized_session: Optional[str]
    if session_id is None:
        sanitized_session = None
    else:
        s = str(session_id).strip()
        sanitized_session = None if s == "" or s.lower() in ("null", "undefined") else s
    ensure_title = message if not sanitized_session else None
    session_id_resolved, _blob_uri, _created = storage.ensure_session(
        agent_id=agent_id,
        session_id=sanitized_session,
        title=ensure_title,
    )
    # Load prior transcript and add current user turn
    transcript = storage.load_transcript(session_id_resolved)
    # Build a mixed history that prefers compact tool messages when present
    mixed_history: List[Dict[str, Any]] = []
    # Convert persisted transcript (full messages) into a form where we prefer compact when both exist.
    # We don't persist compact markers; compact messages are created during runtime. So here we keep transcript as-is.
    mixed_history = transcript
    prompt_history_and_user = mixed_history + [{"role": "user", "content": message, "created_at": _now_epoch()}]
    return StreamingResponse(
        _stream_run_with_storage(prompt_history_and_user, session_id_resolved, storage),
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
@router.get("/agents/{agent_id}/sessions")
async def list_agent_sessions(agent_id: str = Path(...), limit: int = 50) -> List[Dict[str, Any]]:
    storage = AzureStorage()
    sessions = storage.list_sessions(agent_id=agent_id, limit=limit)
    return sessions


def _transcript_to_chat_entries(messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Convert persisted JSONL transcript into ChatEntry[] shape expected by UI.

    Groups sequences of (user) [assistant tool_calls]* [tool results]* (assistant final) into runs.
    """
    runs: List[Dict[str, Any]] = []
    i = 0
    n = len(messages)
    while i < n:
        msg = messages[i]
        if msg.get("role") == "user":
            user_created = int(msg.get("created_at", _now_epoch()))
            run = {
                "message": {
                    "role": "user",
                    "content": msg.get("content") or "",
                    "created_at": user_created,
                }
            }
            i += 1
            # Optionally skip assistant tool_calls message and tool results
            # until we find final assistant content
            while i < n and messages[i].get("role") in ("assistant", "tool"):
                # Stop when we hit assistant with content (final)
                if messages[i].get("role") == "assistant" and messages[i].get("content") not in (None, ""):
                    break
                i += 1
            if i < n and messages[i].get("role") == "assistant":
                assistant = messages[i]
                run["response"] = {
                    "content": assistant.get("content") or "",
                    "created_at": int(assistant.get("created_at", _now_epoch())),
                }
                runs.append(run)
                i += 1
            else:
                # No assistant response found; push partial run
                run["response"] = {
                    "content": "",
                    "created_at": _now_epoch(),
                }
                runs.append(run)
        else:
            i += 1
    return runs


@router.get("/agents/{agent_id}/sessions/{session_id}")
async def get_agent_session(agent_id: str = Path(...), session_id: str = Path(...)) -> Dict[str, Any]:
    storage = AzureStorage()
    transcript = storage.load_transcript(session_id=session_id)
    runs = _transcript_to_chat_entries(transcript)
    # Provide an overall token count for this transcript
    try:
        cheat_sheet = build_tool_cheat_sheet()
        system_msg = {"role": "system", "content": cheat_sheet}
        token_count = _approx_token_count("gpt-4o-azure", [system_msg] + transcript)
    except Exception:
        token_count = None
    return {
        "session_id": session_id,
        "agent_id": agent_id,
        "user_id": None,
        "runs": runs,
        "memory": {"runs": runs},
        "extra_data": {"token_count": token_count} if token_count is not None else {},
        "agent_data": {},
    }


@router.delete("/agents/{agent_id}/sessions/{session_id}")
async def delete_agent_session(agent_id: str = Path(...), session_id: str = Path(...)) -> JSONResponse:
    storage = AzureStorage()
    storage.delete_session(session_id=session_id)
    return JSONResponse(status_code=204, content=None)

