import os
import uuid
import json
from typing import Any, Dict, Optional

import requests
import lusid


class HoneycombClient:
    """Thin client for Honeycomb Luminesce endpoints using LUSID bearer.

    - Base URL from env HONEYCOMB_BASE (default: https://simpleflow.lusid.com/honeycomb)
    - Reuses access token from a provided lusid.ApiClientFactory
    - Uses requests under the hood; callers may run in executor for async contexts
    """

    def __init__(self, api_factory: Optional[lusid.ApiClientFactory] = None, base_url: Optional[str] = None):
        self._api_factory = api_factory
        self.base_url = (base_url or os.getenv("HONEYCOMB_BASE") or "https://simpleflow.lusid.com/honeycomb").rstrip("/")
        self._timeout = int(os.getenv("HONEYCOMB_HTTP_TIMEOUT_SECONDS", "300"))

    def _get_access_token(self) -> str:
        if self._api_factory is None:
            raise RuntimeError("LUSID ApiClientFactory not initialised")
        api = self._api_factory.build(lusid.ApplicationMetadataApi)
        cfg = api.api_client.configuration
        token = getattr(cfg, "access_token", None)
        if not token:
            try:
                _ = api.get_lusid_versions()
                token = getattr(api.api_client.configuration, "access_token", None)
            except Exception:
                token = getattr(api.api_client.configuration, "access_token", None)
        if not token:
            raise RuntimeError("Empty LUSID access token")
        return str(token)

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self._get_access_token()}",
            "Content-Type": "application/json",
        }

    def execute_sql_json(
        self,
        sql: str,
        scalar_parameters: Optional[Dict[str, Any]] = None,
        query_name: Optional[str] = None,
        json_proper: bool = True,
    ) -> Dict[str, Any]:
        """POST /api/Sql/json with provided SQL and parameters.

        According to Honeycomb docs, jsonProper is a query parameter; set true by default.
        scalarParameters are accepted; some tenants also accept Parameters; we send both.
        """
        url = f"{self.base_url}/api/Sql/json"
        params = {"jsonProper": str(json_proper).lower()}
        payload: Dict[str, Any] = {
            "Sql": sql,
            "QueryName": query_name or f"Fathom.Query.{str(uuid.uuid4())[:8]}",
            "scalarParameters": scalar_parameters or {},
            "Parameters": scalar_parameters or {},
        }
        resp = requests.post(url, params=params, headers=self._headers(), json=payload, timeout=self._timeout)
        resp.raise_for_status()
        return resp.json()

    def get_catalog_fields(self, table_like: str) -> Dict[str, Any]:
        """GET /api/Catalog/fields?tableLike=... returns JSON with table/field metadata."""
        url = f"{self.base_url}/api/Catalog/fields"
        params = {"tableLike": table_like}
        resp = requests.get(url, params=params, headers=self._headers(), timeout=self._timeout)
        resp.raise_for_status()
        return resp.json()


