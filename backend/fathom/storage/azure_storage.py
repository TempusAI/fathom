from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

from azure.identity import DefaultAzureCredential
from azure.storage.blob import ContainerClient, BlobClient
from azure.core.exceptions import ResourceNotFoundError
from azure.data.tables import TableServiceClient


TABLE_NAME = "FathomSessions"
BLOB_CONTAINER = "fathom-messages"


def _epoch_now() -> int:
    return int(datetime.now(tz=timezone.utc).timestamp())


def _yyyymmdd(dt: Optional[datetime] = None) -> str:
    d = dt or datetime.now(tz=timezone.utc)
    return d.strftime("%Y%m%d")


class AzureStorage:
    def __init__(self) -> None:
        self._credential = DefaultAzureCredential()

        blob_account_url = os.environ.get("AZURE_BLOB_ACCOUNT_URL")
        table_account_url = os.environ.get("AZURE_TABLE_ACCOUNT_URL")
        if not blob_account_url or not table_account_url:
            raise RuntimeError(
                "Missing AZURE_BLOB_ACCOUNT_URL or AZURE_TABLE_ACCOUNT_URL environment variables"
            )

        # Blob container (append blob per session)
        self._container = ContainerClient(
            account_url=blob_account_url,
            container_name=BLOB_CONTAINER,
            credential=self._credential,
        )
        try:
            self._container.create_container()
        except Exception:
            # Already exists
            pass

        # Table service (for sessions index)
        self._tables = TableServiceClient(
            endpoint=table_account_url,
            credential=self._credential,
        )
        try:
            self._tables.create_table_if_not_exists(TABLE_NAME)
        except Exception:
            # Already exists
            pass

    # -------- Transcript blob helpers --------
    def _blob_client(self, session_id: str) -> BlobClient:
        # Build blob URL from container URL
        blob_url = f"{self._container.url}/{session_id}.jsonl"
        return BlobClient.from_blob_url(blob_url=blob_url, credential=self._credential)

    def load_transcript(self, session_id: str) -> List[Dict[str, Any]]:
        client = self._blob_client(session_id)
        try:
            # Download full blob content; if not exists, return empty
            downloader = client.download_blob()
            data = downloader.readall()
            text = data.decode("utf-8")
        except Exception:
            return []

        messages: List[Dict[str, Any]] = []
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                messages.append(json.loads(line))
            except Exception:
                # Skip malformed JSONL lines
                continue
        return messages

    def append_messages(self, session_id: str, new_messages: List[Dict[str, Any]]) -> None:
        if not new_messages:
            return
        client = self._blob_client(session_id)
        payload = "\n".join(json.dumps(m, ensure_ascii=False) for m in new_messages) + "\n"
        data = payload.encode("utf-8")
        # Try upload without overwrite; if blob exists, read-append-reupload
        try:
            client.upload_blob(data, overwrite=False)
            return
        except Exception:
            # Likely exists; fall back to read+append+overwrite
            try:
                existing = client.download_blob().readall()
            except ResourceNotFoundError:
                existing = b""
            combined = existing + data
            client.upload_blob(combined, overwrite=True)

    # -------- Sessions table helpers --------
    def _table(self):
        return self._tables.get_table_client(TABLE_NAME)

    def session_exists(self, session_id: str) -> bool:
        table = self._table()
        try:
            # RowKey is session_id; PartitionKey varies by day, so search by RowKey
            entities = table.query_entities(query_filter=f"RowKey eq '{session_id}'", results_per_page=1)
            for _ in entities:
                return True
            return False
        except Exception:
            return False

    def create_session(self, agent_id: str, title: Optional[str] = None) -> Tuple[str, str]:
        session_id = str(uuid.uuid4())
        partition = _yyyymmdd()
        created_at = _epoch_now()
        table = self._table()
        entity = {
            "PartitionKey": partition,
            "RowKey": session_id,
            "AgentId": agent_id,
            "Title": title or "",
            # Container URL already includes the container name
            "MessagesBlobUri": f"{self._container.url}/{session_id}.jsonl",
            "CreatedAt": created_at,
            "UpdatedAt": created_at,
            "MessageCount": 0,
        }
        table.create_entity(entity=entity)
        return session_id, entity["MessagesBlobUri"]

    def touch_session(self, session_id: str, increment_messages_by: int = 0) -> None:
        table = self._table()
        # Fetch entity by RowKey (session_id); PartitionKey unknown → query
        try:
            entities = list(table.query_entities(query_filter=f"RowKey eq '{session_id}'", results_per_page=1))
            if not entities:
                return
            entity = entities[0]
            entity["UpdatedAt"] = _epoch_now()
            if increment_messages_by:
                try:
                    entity["MessageCount"] = int(entity.get("MessageCount", 0)) + increment_messages_by
                except Exception:
                    entity["MessageCount"] = increment_messages_by
            table.update_entity(entity=entity, mode="Merge")
        except Exception:
            return

    def ensure_session(self, agent_id: str, session_id: Optional[str], title: Optional[str]) -> Tuple[str, str, bool]:
        table = self._table()
        if session_id:
            # If the session exists, reuse it. If not, create a row with this exact RowKey to avoid changing the session id.
            if self.session_exists(session_id):
                return session_id, f"{self._container.url}/{session_id}.jsonl", False
            # Upsert a new entity with provided session_id
            entity = {
                "PartitionKey": _yyyymmdd(),
                "RowKey": session_id,
                "AgentId": agent_id,
                "Title": title or "",
                "MessagesBlobUri": f"{self._container.url}/{session_id}.jsonl",
                "CreatedAt": _epoch_now(),
                "UpdatedAt": _epoch_now(),
                "MessageCount": 0,
            }
            try:
                table.create_entity(entity=entity)
            except Exception:
                try:
                    table.update_entity(entity=entity, mode="Merge")
                except Exception:
                    pass
            return session_id, entity["MessagesBlobUri"], True
        new_session_id, blob_uri = self.create_session(agent_id=agent_id, title=title)
        return new_session_id, blob_uri, True

    def list_sessions(self, agent_id: str, days: int = 14, limit: int = 50) -> List[Dict[str, Any]]:
        table = self._table()
        # Filter by AgentId and date window via PartitionKey
        end = datetime.now(tz=timezone.utc)
        start = end - timedelta(days=days)
        start_key = _yyyymmdd(start)
        end_key = _yyyymmdd(end)
        # Note: Azure Tables ignores order by; we'll sort client-side
        filter_expr = f"(PartitionKey ge '{start_key}' and PartitionKey le '{end_key}') and AgentId eq '{agent_id}'"
        entities = list(table.query_entities(query_filter=filter_expr))
        # Sort by UpdatedAt desc
        entities.sort(key=lambda e: int(e.get("UpdatedAt", 0)), reverse=True)
        out: List[Dict[str, Any]] = []
        for e in entities[:limit]:
            out.append({
                "session_id": e.get("RowKey"),
                "title": e.get("Title", ""),
                "created_at": int(e.get("CreatedAt", 0)),
            })
        return out

    def delete_session(self, session_id: str) -> None:
        # Resolve all entities to get PartitionKey(s), then delete row(s) and blob
        table = self._table()
        try:
            entities = list(table.query_entities(query_filter=f"RowKey eq '{session_id}'"))
            for entity in entities:
                try:
                    table.delete_entity(partition_key=entity["PartitionKey"], row_key=entity["RowKey"])
                except Exception:
                    continue
        except Exception:
            pass

        # Delete blob
        client = self._blob_client(session_id)
        try:
            client.delete_blob()
        except Exception:
            pass


