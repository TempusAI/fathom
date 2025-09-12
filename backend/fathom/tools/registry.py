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
                    "Get Honeycomb Catalog fields for matching tables. "
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
                    "Execute Luminesce SQL and return a compact result (columns, row_count, sample_rows up to 10). "
                    "Prefer selecting specific columns and filtering by identifiers to keep results small."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "sql": {"type": "string", "description": "The Luminesce SQL to execute."},
                        "scalarParameters": {
                            "type": "object",
                            "description": "Optional scalar parameters (key-value) for the SQL execution.",
                            "additionalProperties": {"type": ["string", "number", "boolean"]},
                        },
                        "queryName": {"type": "string", "description": "Optional query name for logs."},
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
        "You can call two tools to investigate LUSID data via Honeycomb (Luminesce).\n"
        "- catalog_get_fields(tableLike): List fields for matching tables (wildcards ok).\n"
        "- sql_execute(sql, scalarParameters?, queryName?): Run Luminesce SQL; returns columns, row_count, sample_rows (≤10).\n"
        "Guidance: Select only required columns; filter using identifiers (e.g., LusidInstrumentId, PortfolioScope/Code); limit result sizes.\n"
        'Parameters: Prefer inlining literals directly in the SQL body for MVP reliability. If you provide scalarParameters, they may be ignored.\n'
        "Examples:\n"
        "- catalog_get_fields('Lusid.Instrument')\n"
        "- sql_execute('select LusidInstrumentId, Name from Lusid.Instrument where LusidInstrumentId = \'LUID_123\'')\n"
        "Use catalog_get_fields before querying unfamiliar tables. Keep queries targeted."
    )


