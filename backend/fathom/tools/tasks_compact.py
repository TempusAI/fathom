from __future__ import annotations

import json
from typing import Any, Dict, List, Tuple


def _as_str(value: Any) -> str:
    try:
        if value is None:
            return ""
        if isinstance(value, (str, int, float, bool)):
            return str(value)
        return json.dumps(value, ensure_ascii=False)
    except Exception:
        try:
            return str(value)
        except Exception:
            return ""


def _truncate(text: str, max_len: int = 256) -> str:
    if len(text) <= max_len:
        return text
    return text[: max_len - 1] + "…"


def _group_by_ultimate_parent(tasks: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    groups: Dict[str, List[Dict[str, Any]]] = {}
    for t in tasks:
        parent = (t.get("ultimateParentTask") or {})
        parent_id = _as_str(parent.get("id") or t.get("id"))
        groups.setdefault(parent_id, []).append(t)
    return groups


def _parent_meta(task: Dict[str, Any]) -> Tuple[str, str, str, List[str]]:
    pid = _as_str(task.get("id"))
    name = _as_str(task.get("taskDefinitionDisplayName"))
    state = _as_str(task.get("state"))
    created = _as_str(((task.get("version") or {}).get("asAtCreated")) or "")
    corr = task.get("correlationIds") or []
    corr_ids = [ _as_str(c) for c in corr if c is not None ]
    return pid, name, state, corr_ids if isinstance(corr_ids, list) else []


def _kv_pairs(d: Dict[str, Any]) -> List[str]:
    pairs: List[str] = []
    for k, v in d.items():
        if v is None:
            continue
        pairs.append(f"{k}={_truncate(_as_str(v))}")
    return pairs


def build_compact_task_context(tasks: List[Dict[str, Any]]) -> str:
    """Return a compact, token-efficient system context for selected tasks.

    Format (pipe-delimited, line-oriented) with a simple header marker so we can
    detect prior persistence and avoid duplication:

    task_context:v1
    parent|<id>|<name>|state:<state>|created:<iso>|children:<count>|corr:<id1,id2>
    task|<id>|<name>|state:<state>|created:<iso>|terminal:<bool>|stack:<key>|corr:<id1,id2>
    fields: <k>=<v> | <k>=<v> | ...
    meta: version.asAtModified=<...> | asAtLastTransition=<...> | actionLogIdCreated=<...> | ...
    (repeat for each task)
    """
    if not isinstance(tasks, list) or len(tasks) == 0:
        return "task_context:v1\n(empty)"

    lines: List[str] = ["task_context:v1"]
    groups = _group_by_ultimate_parent(tasks)

    for parent_id, group_tasks in groups.items():
        # Choose a representative parent (prefer the one whose id == parent_id)
        parent = next((t for t in group_tasks if _as_str(t.get("id")) == parent_id), group_tasks[0])
        pid, pname, pstate, pcorr = _parent_meta(parent)
        pcreated = _as_str(((parent.get("version") or {}).get("asAtCreated")) or "")
        lines.append(
            "|".join(
                [
                    "parent",
                    pid,
                    _truncate(pname, 160),
                    f"state:{_truncate(pstate, 64)}",
                    f"created:{_truncate(pcreated, 64)}",
                    f"children:{max(0, len(group_tasks) - 1)}",
                    f"corr:{','.join(pcorr)}",
                ]
            )
        )

        for t in group_tasks:
            tid = _as_str(t.get("id"))
            tname = _as_str(t.get("taskDefinitionDisplayName"))
            tstate = _as_str(t.get("state"))
            tcreated = _as_str(((t.get("version") or {}).get("asAtCreated")) or "")
            terminal = _as_str(t.get("terminalState"))
            stack = _as_str(t.get("stackingKey") or "")
            corr = t.get("correlationIds") or []
            tcorr = [ _as_str(c) for c in corr if c is not None ]

            lines.append(
                "|".join(
                    [
                        "task",
                        tid,
                        _truncate(tname, 160),
                        f"state:{_truncate(tstate, 64)}",
                        f"created:{_truncate(tcreated, 64)}",
                        f"terminal:{terminal}",
                        f"stack:{_truncate(stack, 64)}",
                        f"corr:{','.join(tcorr)}",
                    ]
                )
            )

            # Fields
            fields = t.get("fields") or []
            if isinstance(fields, list) and fields:
                kv = []
                for f in fields:
                    name = _as_str((f or {}).get("name"))
                    val = _truncate(_as_str((f or {}).get("value")))
                    if name:
                        kv.append(f"{name}={val}")
                if kv:
                    lines.append("fields: " + " | ".join(kv))

            # Other meta (compact key-value selection)
            meta: Dict[str, Any] = {}
            meta["asAtLastTransition"] = t.get("asAtLastTransition")
            meta["actionLogIdCreated"] = t.get("actionLogIdCreated")
            meta["actionLogIdModified"] = t.get("actionLogIdModified")
            meta["actionLogIdSubmitted"] = t.get("actionLogIdSubmitted")
            version = t.get("version") or {}
            if isinstance(version, dict):
                for k in ("asAtModified", "userIdCreated", "userIdModified", "asAtVersionNumber"):
                    if version.get(k) is not None:
                        meta[f"version.{k}"] = version.get(k)
            kv = _kv_pairs({k: v for k, v in meta.items() if v is not None})
            if kv:
                lines.append("meta: " + " | ".join(kv))

    return "\n".join(lines)


