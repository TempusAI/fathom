from __future__ import annotations

import json
from typing import Any, Dict, List


def _truncate(text: str, max_len: int = 160) -> str:
    if len(text) <= max_len:
        return text
    return text[: max_len - 1] + "…"


def compact_catalog_get_fields(result: Dict[str, Any], args: Dict[str, Any]) -> str:
    table_like = result.get("table_like") or args.get("table_like") or ""
    lines: List[str] = []
    lines.append(f"tool: catalog_get_fields  table_like: {table_like}")
    catalog = result.get("catalog") or []
    # One line per field: name|type|desc
    for f in catalog:
        name = (f.get("FieldName") or "").strip()
        dtype = (f.get("DataType") or "").strip()
        desc = (f.get("Description") or "").strip()
        if not name and not dtype and not desc:
            continue
        lines.append(f"{name}|{dtype}|{_truncate(desc)}")
    # Indicate if there is more per the summary flag (best-effort)
    schema = result.get("schema") or {}
    has_more = schema.get("has_more") or {}
    if isinstance(has_more, dict):
        for t, more in has_more.items():
            if more:
                lines.append(f"has_more:{t}")
                break
    return "\n".join(lines)


def compact_sql_execute(result: Dict[str, Any], args: Dict[str, Any]) -> str:
    # Keep args verbatim (sql + scalar_parameters) per requirements
    sql = args.get("sql") or result.get("executedSql") or ""
    scalar_parameters = args.get("scalar_parameters")
    if isinstance(scalar_parameters, (dict, list)):
        scalar_args = json.dumps(scalar_parameters, ensure_ascii=False)
    else:
        scalar_args = str(scalar_parameters) if scalar_parameters is not None else ""

    lines: List[str] = []
    lines.append("tool: sql_execute")
    if sql:
        lines.append("args.sql:")
        lines.append(sql.strip())
    if scalar_args:
        lines.append("args.scalar_parameters:")
        lines.append(scalar_args)

    row_count = int(result.get("row_count") or 0)
    lines.append(f"row_count:{row_count}")

    # Include ALL sample rows, without column names, as pipe-delimited values for compactness
    sample_rows = result.get("sample_rows") or []
    # Determine a stable key order (sorted) if dict rows
    key_order: List[str] = []
    if sample_rows and isinstance(sample_rows[0], dict):
        key_order = sorted(sample_rows[0].keys())
    lines.append("sample_rows:")
    for row in sample_rows:
        if isinstance(row, dict):
            values = [row.get(k, "") for k in key_order]
            lines.append(" | ".join(str(v) for v in values))
        elif isinstance(row, list):
            lines.append(" | ".join(str(v) for v in row))
        else:
            # Fallback string form
            try:
                lines.append(json.dumps(row, ensure_ascii=False))
            except Exception:
                lines.append(str(row))

    return "\n".join(lines)


def build_prompt_context(tool_name: str, result: Dict[str, Any], args: Dict[str, Any]) -> str:
    name = (tool_name or "").strip().lower()
    if name == "catalog_get_fields":
        return compact_catalog_get_fields(result, args)
    if name == "sql_execute":
        return compact_sql_execute(result, args)
    # Fallback: compact key info
    summary = {k: v for k, v in result.items() if isinstance(v, (int, float, str))}
    return f"tool: {tool_name}\n" + "\n".join(f"{k}:{summary[k]}" for k in summary)


