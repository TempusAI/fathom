from __future__ import annotations

import json
import time
from typing import Any, Dict, List, Optional, Tuple
import difflib

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
    """Get Honeycomb Catalog fields with cache support and compact summary.

    - If exact table cached, serve from cache (no network).
    - On wildcard or cache miss, fetch from Honeycomb, cache per TableName, and return.
    - Also include a compact per-table summary (pk, ids, name, status, dates, measures, other; top 12 only).
    """
    started_at = time.time()
    results: List[Dict[str, Any]] = []
    is_wildcard = any(ch in table_like for ch in ["%", "*"])

    if not is_wildcard:
        cached = _SCHEMA_CACHE.get(table_like)
        if cached:
            for f in cached.get("fields") or []:
                item = dict(f)
                item["TableName"] = table_like
                results.append(item)
        else:
            client = _get_honeycomb_client(api_factory)
            fetched = client.get_catalog_fields(table_like)
            if isinstance(fetched, list):
                by_table: Dict[str, List[Dict[str, Any]]] = {}
                for item in fetched:
                    tname = item.get("TableName") or table_like
                    by_table.setdefault(tname, []).append(item)
                for t, fields in by_table.items():
                    _SCHEMA_CACHE.set(t, fields)
                results = fetched
    else:
        client = _get_honeycomb_client(api_factory)
        fetched = client.get_catalog_fields(table_like)
        if isinstance(fetched, list):
            by_table: Dict[str, List[Dict[str, Any]]] = {}
            for item in fetched:
                tname = item.get("TableName") or ""
                if tname:
                    by_table.setdefault(tname, []).append(item)
            for t, fields in by_table.items():
                _SCHEMA_CACHE.set(t, fields)
            results = fetched

    duration_ms = int((time.time() - started_at) * 1000)

    # Build compact summary from cache
    by_table_summary: Dict[str, Dict[str, List[str]]] = {}
    names_by_table: Dict[str, List[str]] = {}
    for item in results:
        t = item.get("TableName") or table_like
        names_by_table.setdefault(t, []).append(item.get("FieldName") or "")
    for t in names_by_table:
        entry = _SCHEMA_CACHE.get(t)
        if entry and entry.get("summary"):
            by_table_summary[t] = {k: (entry["summary"].get(k) or [])[:12] for k in entry["summary"]}
        else:
            by_table_summary[t] = {"all": names_by_table[t][:12]}

    return {
        "table_like": table_like,
        "duration_ms": duration_ms,
        "catalog": results,
        "schema": {"by_table": by_table_summary, "has_more": {t: len(names_by_table.get(t, [])) > 12 for t in names_by_table}},
    }


class SchemaCache:
    def __init__(self, ttl_seconds: int = 1800) -> None:
        self._ttl_seconds = ttl_seconds
        self._table_to_entry: Dict[str, Dict[str, Any]] = {}

    def now(self) -> float:
        return time.time()

    def _key(self, table: str) -> str:
        return table.strip().lower()

    def set(self, table: str, fields: List[Dict[str, Any]]) -> None:
        entry = {
            "fields": fields,
            "summary": _summarize_fields(fields),
            "ts": self.now(),
        }
        self._table_to_entry[self._key(table)] = entry

    def get(self, table: str) -> Optional[Dict[str, Any]]:
        entry = self._table_to_entry.get(self._key(table))
        if not entry:
            return None
        if self.now() - entry["ts"] > self._ttl_seconds:
            return None
        return entry

    def list_tables(self) -> List[str]:
        return list(self._table_to_entry.keys())


def _categorize_field(name: str, data_type: str, is_pk: int | bool, is_main: int | bool) -> str:
    n = (name or "").lower()
    if is_pk:
        return "pk"
    if any(k in n for k in ["lusidinstrumentid", "instrumentid", "id", "code", "isin", "figi", "sedol", "ric", "cusip"]):
        return "ids"
    if n in ("name", "displayname"):
        return "name"
    if n in ("state", "isactive"):
        return "status"
    if "date" in n or "asat" in n:
        return "dates"
    if (data_type or "").lower() in ("int", "decimal", "double", "number"):
        return "measures"
    return "other"


def _summarize_fields(fields: List[Dict[str, Any]]) -> Dict[str, List[str]]:
    groups: Dict[str, List[str]] = {k: [] for k in ["pk", "ids", "name", "status", "dates", "measures", "other"]}
    for f in fields:
        cat = _categorize_field(
            f.get("FieldName") or f.get("name") or "",
            f.get("DataType") or f.get("type") or "",
            f.get("IsPrimaryKey") or 0,
            f.get("IsMain") or 0,
        )
        groups[cat].append(f.get("FieldName") or f.get("name") or "")
    return groups


_SCHEMA_CACHE = SchemaCache()


def prewarm_schema_cache(api_factory: lusid.ApiClientFactory | None, tables: List[str]) -> None:
    client = _get_honeycomb_client(api_factory)
    for t in tables:
        try:
            cat = client.get_catalog_fields(t)
            # Expecting a list of field dicts; if API returns wrapper, unwrap best-effort
            fields = cat if isinstance(cat, list) else cat.get("values") if isinstance(cat, dict) else []
            _SCHEMA_CACHE.set(t, fields or [])
        except Exception:
            continue


def _schema_summary_for_tables(tables: List[str], top_n: int = 12, main_only: bool = True) -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
    schemas: Dict[str, Any] = {}
    has_more: Dict[str, bool] = {}
    for t in tables:
        entry = _SCHEMA_CACHE.get(t)
        if not entry:
            suggestions = difflib.get_close_matches(t.strip().lower(), _SCHEMA_CACHE.list_tables(), n=5, cutoff=0.3)
            err = {
                "code": "SCHEMA_NOT_FOUND",
                "message": f"No cached schema for '{t}'. Use catalog_get_fields(tableLike) to discover or choose a suggestion.",
                "did_you_mean": suggestions,
            }
            return None, err
        fields = entry.get("fields") or []
        if main_only:
            fields = [f for f in fields if (f.get("IsMain") or 0) == 1 or (f.get("IsPrimaryKey") or 0) == 1]
        names = [(f.get("FieldName") or f.get("name") or "") for f in fields]
        summary = entry.get("summary") or {}
        schemas[t] = {
            "pk": (summary.get("pk") or [])[:top_n],
            "ids": (summary.get("ids") or [])[:top_n],
            "name": (summary.get("name") or [])[:top_n],
            "status": (summary.get("status") or [])[:top_n],
            "dates": (summary.get("dates") or [])[:top_n],
            "measures": (summary.get("measures") or [])[:top_n],
            "other": (summary.get("other") or [])[:top_n],
            "all": names[:top_n],
        }
        has_more[t] = len(names) > top_n
    return {"by_table": schemas, "has_more": has_more}, None


def run_sql_execute(
    api_factory: lusid.ApiClientFactory | None,
    sql: Optional[str] = None,
    scalar_parameters: Optional[Dict[str, Any]] = None,
    query_name: Optional[str] = None,
    sample_limit: int = 10,
    tables: Optional[List[str]] = None,
    mode: Optional[str] = None,
    topN: int = 12,
    mainOnly: bool = True,
) -> Dict[str, Any]:
    """Combined schema + SQL tool (keeps the same name for the agent).

    - If only tables provided or mode=='schema': return cached schema summary.
    - If sql provided and mode in (None, 'both', 'execute'): execute SQL; if tables provided, also include schema summary.
    - On cache miss: return SCHEMA_NOT_FOUND with did_you_mean suggestions.
    """
    include_schema_only = (sql is None) or (mode == "schema")
    include_both = sql is not None and (mode in (None, "both"))
    include_execute_only = sql is not None and mode == "execute"

    def _extract_tables_from_sql(q: str) -> List[str]:
        import re
        candidates: List[str] = []
        for kw in [r"\bfrom\b", r"\bjoin\b"]:
            for m in re.finditer(kw + r"\s+([A-Za-z0-9_.]+)", q, flags=re.IGNORECASE):
                name = m.group(1)
                # Strip trailing punctuation/alias
                name = name.strip().rstrip(",;")
                candidates.append(name)
        # Deduplicate, preserve order
        seen = set()
        ordered: List[str] = []
        for c in candidates:
            lc = c.lower()
            if lc not in seen:
                seen.add(lc)
                ordered.append(c)
        return ordered

    schema_block: Optional[Dict[str, Any]] = None
    # If caller asked for schema and didn't pass tables, try to infer from SQL
    if (mode == "schema") and not tables and sql:
        inferred = _extract_tables_from_sql(sql)
        tables = inferred if inferred else None

    if tables:
        schema_block, err = _schema_summary_for_tables(tables, top_n=topN, main_only=mainOnly)
        if err is not None:
            return {"error": err}
        if include_schema_only and not include_both and not include_execute_only:
            return {"schema": schema_block}

    if sql is None:
        return {"schema": schema_block} if schema_block else {"message": "No SQL provided."}

    client = _get_honeycomb_client(api_factory)
    # Normalize scalar parameters (accepted input; currently not sent downstream as we inline literals)
    normalized_params: Dict[str, Any] = {}
    if isinstance(scalar_parameters, dict):
        normalized_params = scalar_parameters
    elif isinstance(scalar_parameters, str) and scalar_parameters.strip():
        raw = scalar_parameters.strip()
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
    result: Dict[str, Any] = {
        "query_name": query_name,
        "duration_ms": duration_ms,
        "row_count": row_count,
        "columns": columns,
        "sample_rows": sample_rows,
        "data": raw if row_count == 0 else None,
        "executedSql": sql,
    }
    if schema_block is not None:
        result["schema"] = schema_block
    return result


