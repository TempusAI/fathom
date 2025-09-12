from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

import lusid

from fathom.tools.sql import run_catalog_get_fields, run_sql_execute


def get_tool_definitions() -> List[Dict[str, Any]]:
    """Return OpenAI/Azure-compatible tool (function) definitions."""
    return [
        {
            "type": "function",
            "function": {
                "name": "catalog_get_fields",
                "description": (
                    "Get Luminesce table fields (column metadata) for matching tables. "
                    "Supports wildcards in tableLike (e.g., 'Lusid.Instrument', 'Lusid.Instrument%', 'Lusid.%')."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "tableLike": {
                            "type": "string",
                            "description": "A table name or pattern with wildcards to filter the catalog.",
                        }
                    },
                    "required": ["tableLike"],
                    "additionalProperties": False,
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "sql_execute",
                "description": (
                    "Execute Luminesce SQL and return a compact result (columns, row_count, sample_rows ≤10). "
                    "Guidance: Prefer select * with a tight WHERE for the first probe, or call catalog_get_fields('Table') to project specific columns."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "sql": {"type": "string", "description": "The Luminesce SQL to execute."},
                        "scalarParameters": {
                            "type": "object",
                            "description": "Optional scalar parameters (key-value). Inlined literals are preferred for MVP.",
                            "additionalProperties": {"type": ["string", "number", "boolean"]},
                        },
                        "queryName": {"type": "string", "description": "Optional query name for logs."}
                    },
                    "required": ["sql"],
                    "additionalProperties": False,
                },
            },
        },
    ]


def execute_tool_call(
    api_factory: Optional[lusid.ApiClientFactory],
    name: str,
    arguments: Dict[str, Any],
) -> Dict[str, Any]:
    """Execute a tool by name with arguments and return JSON serialisable result."""
    if name == "catalog_get_fields":
        table_like = str(arguments.get("tableLike", "")).strip()
        if not table_like:
            raise ValueError("Missing required argument: tableLike")
        return run_catalog_get_fields(api_factory, table_like)

    if name == "sql_execute":
        sql = str(arguments.get("sql", "")).strip()
        if not sql:
            raise ValueError("Missing required argument: sql")
        scalar_params = arguments.get("scalarParameters") or {}
        query_name = arguments.get("queryName")
        return run_sql_execute(api_factory, sql=sql, scalar_parameters=scalar_params, query_name=query_name, sample_limit=10)

    raise ValueError(f"Unknown tool: {name}")


def build_tool_cheat_sheet() -> str:
    """Compact system prompt describing tools and best practices (token-efficient)."""
    return (
        "Tools for exploring LUSID via Luminesce SQL:\n"
        "- catalog_get_fields(tableLike): Return cached-or-fetched field lists with a compact summary.\n"
        "- sql_execute(sql, scalarParameters?, queryName?): Execute SQL (results are compact).\n"
        "Guidance: Prefer select * with a tight WHERE for the first probe, or call catalog_get_fields('Table') first to project specific columns.\n"
        'Parameters: Prefer inlining literals directly in the SQL body for MVP reliability. scalarParameters may be ignored.\n'
        "Examples:\n"
        "- sql_execute('select * from Lusid.Instrument where LusidInstrumentId=\\'LUID_123\\'')\n"
        "- catalog_get_fields('Lusid.Instrument')\n"
        "Common tables (quick context):\n"
        "- Lusid.Instrument: Instrument master (IDs, DisplayName, Type, State, Scope, AsAt, EffectiveAt).\n"
        "- Lusid.Instrument.Quote: Quotes by instrument/provider/date (Bid/Ask/Mid, Ccy, Source).\n"
        "- Lusid.Portfolio: Portfolio entities (Scope, Code, Name, Type, created/modified timestamps).\n"
        "- Lusid.Portfolio.Holding: Holdings/positions (Scope, Code, LusidInstrumentId, Quantity/Cost, Ccy, AsAt, EffectiveAt).\n"
        "- Lusid.Portfolio.Txn: Transactions (Trade/Settle dates, Instrument, Quantity, Consideration, TxnType).\n"
        "- Scheduler.Schedule: Scheduled SQL jobs (QueryName, Cron/NextRun, Enabled, Status).\n"
        "Use catalog_get_fields before querying unfamiliar tables. Keep queries targeted."
    )


