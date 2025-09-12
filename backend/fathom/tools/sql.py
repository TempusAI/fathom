from __future__ import annotations

import json
import time
from typing import Any, Dict, List, Optional, Tuple

import lusid

from fathom.clients.honeycomb_client import HoneycombClient


def _get_honeycomb_client(api_factory: lusid.ApiClientFactory | None) -> HoneycombClient:
    return HoneycombClient(api_factory=api_factory)


def _summarize_tabular_result(data: Any, sample_limit: int = 10) -> Tuple[List[str], List[Dict[str, Any]], int]:
    """Try to infer columns, sample rows, and row count from Honeycomb JSON.

    This is resilient to differing shapes by checking common patterns.
    """
    # Pattern 1: { "Tables": [ { "Columns": [...], "Rows": [...] } ] }
    if isinstance(data, dict) and "Tables" in data and isinstance(data["Tables"], list) and data["Tables"]:
        table = data["Tables"][0]
        rows = table.get("Rows") or []
        cols = table.get("Columns") or []
        columns = [c.get("Name") if isinstance(c, dict) else str(c) for c in cols]
        if rows and isinstance(rows[0], dict):
            sample = rows[:sample_limit]
            return columns, sample, len(rows)
        if rows and isinstance(rows[0], list):
            # Convert list rows to dicts using columns if available
            sample = []
            for r in rows[:sample_limit]:
                row_dict = {columns[i] if i < len(columns) else f"col_{i}": r[i] for i in range(len(r))}
                sample.append(row_dict)
            return columns, sample, len(rows)

    # Pattern 2: { "columns": [...], "rows": [...] }
    if isinstance(data, dict) and "rows" in data:
        rows = data.get("rows") or []
        columns = data.get("columns") or []
        if rows and isinstance(rows[0], dict):
            sample = rows[:sample_limit]
            return [str(c) for c in columns] if columns else list(sample[0].keys()), sample, len(rows)
        if rows and isinstance(rows[0], list):
            cols = [str(c) for c in columns]
            sample = []
            for r in rows[:sample_limit]:
                row_dict = {cols[i] if i < len(cols) else f"col_{i}": r[i] for i in range(len(r))}
                sample.append(row_dict)
            return cols, sample, len(rows)

    # Pattern 3: List[Dict]
    if isinstance(data, list) and data and isinstance(data[0], dict):
        sample = data[:sample_limit]
        columns = list({k for row in sample for k in row.keys()})
        return columns, sample, len(data)

    # Fallback: unstructured
    return [], [], 0


def run_catalog_get_fields(api_factory: lusid.ApiClientFactory | None, table_like: str) -> Dict[str, Any]:
    """Call Honeycomb Catalog fields endpoint and return JSON.

    table_like supports wildcards (e.g., 'Lusid.Instrument', 'Lusid.Instrument%').
    """
    client = _get_honeycomb_client(api_factory)
    started_at = time.time()
    catalog = client.get_catalog_fields(table_like)
    duration_ms = int((time.time() - started_at) * 1000)
    # Return raw catalog to retain fidelity; caller/model should narrow tableLike to reduce size.
    return {
        "table_like": table_like,
        "duration_ms": duration_ms,
        "catalog": catalog,
    }


def run_sql_execute(
    api_factory: lusid.ApiClientFactory | None,
    sql: str,
    scalar_parameters: Optional[Dict[str, Any]] = None,
    query_name: Optional[str] = None,
    sample_limit: int = 10,
) -> Dict[str, Any]:
    """Execute arbitrary Luminesce SQL and return compact results suitable for LLM context."""
    client = _get_honeycomb_client(api_factory)
    # Normalize scalar parameters: accept dict or string; ensure JSON object for Honeycomb
    normalized_params: Dict[str, Any] = {}
    if isinstance(scalar_parameters, dict):
        normalized_params = scalar_parameters
    elif isinstance(scalar_parameters, str) and scalar_parameters.strip():
        raw = scalar_parameters.strip()
        # Replace single quotes with double quotes if needed, then attempt to parse
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, dict):
                normalized_params = parsed
        except Exception:
            try:
                repaired = raw.replace("'", '"')
                parsed = json.loads(repaired)
                if isinstance(parsed, dict):
                    normalized_params = parsed
            except Exception:
                normalized_params = {}
    started_at = time.time()
    raw = client.execute_sql_json(sql=sql, scalar_parameters=normalized_params, query_name=query_name, json_proper=True)
    duration_ms = int((time.time() - started_at) * 1000)

    columns, sample_rows, row_count = _summarize_tabular_result(raw, sample_limit=sample_limit)
    return {
        "query_name": query_name,
        "duration_ms": duration_ms,
        "row_count": row_count,
        "columns": columns,
        "sample_rows": sample_rows,
        "data": raw if row_count == 0 else None,
    }


