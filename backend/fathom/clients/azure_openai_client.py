from __future__ import annotations

import os
import json
from dataclasses import dataclass
from typing import Any, AsyncGenerator, Dict, List, Optional

import aiohttp
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from azure.keyvault.secrets import SecretClient


COGNITIVE_SERVICES_SCOPE = "https://cognitiveservices.azure.com/.default"


@dataclass
class AzureOpenAIConfig:
    endpoint: str
    deployment: str
    api_version: str
    tenant_id: Optional[str] = None
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    key_vault_name: Optional[str] = None
    key_vault_secret_name: str = "AZURE-CLIENT-SECRET"
    api_key: Optional[str] = None
    key_vault_api_key_name: str = "AZURE-OPENAI-API-KEY"


def _get_env(name: str, default: Optional[str] = None) -> Optional[str]:
    value = os.getenv(name, default)
    if value is not None:
        value = value.strip()
    return value


def load_azure_openai_config() -> AzureOpenAIConfig:
    """Load Azure OpenAI configuration from environment and (optionally) Key Vault.

    Environment variables used:
    - AZURE_OPENAI_ENDPOINT (required)
    - AZURE_OPENAI_DEPLOYMENT (required)
    - AZURE_OPENAI_API_VERSION (required)
    - AZURE_TENANT_ID, AZURE_CLIENT_ID, AZURE_CLIENT_SECRET (optional)
    - KEY_VAULT_NAME (optional; if provided and CLIENT_SECRET is missing, attempts KV)
    - KEY_VAULT_CLIENT_SECRET_NAME (optional; default 'AZURE-CLIENT-SECRET')
    """
    endpoint = _get_env("AZURE_OPENAI_ENDPOINT")
    deployment = _get_env("AZURE_OPENAI_DEPLOYMENT")
    api_version = _get_env("AZURE_OPENAI_API_VERSION") or "2024-12-01-preview"
    tenant_id = _get_env("AZURE_TENANT_ID")
    client_id = _get_env("AZURE_CLIENT_ID")
    client_secret = _get_env("AZURE_CLIENT_SECRET")
    api_key = _get_env("AZURE_OPENAI_API_KEY")
    key_vault_name = _get_env("KEY_VAULT_NAME") or _get_env("AZURE_KEY_VAULT_NAME") or _get_env("KEY_VAULT")
    key_vault_secret_name = _get_env("KEY_VAULT_CLIENT_SECRET_NAME", "AZURE-CLIENT-SECRET")
    key_vault_api_key_name = _get_env("KEY_VAULT_AOAI_API_KEY_NAME", "AZURE-OPENAI-API-KEY")

    if not endpoint or not deployment or not api_version:
        raise RuntimeError(
            "Missing required Azure OpenAI env vars: AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_DEPLOYMENT, AZURE_OPENAI_API_VERSION"
        )

    # Optional: attempt to fetch client secret and/or AOAI API key from Key Vault if missing
    if not client_secret and key_vault_name:
        try:
            vault_uri = f"https://{key_vault_name}.vault.azure.net"
            credential = DefaultAzureCredential()
            kv_client = SecretClient(vault_url=vault_uri, credential=credential)
            secret_bundle = kv_client.get_secret(key_vault_secret_name)
            client_secret = secret_bundle.value
        except Exception:
            # Non-fatal; proceed without secret (EnvironmentCredential may still work via other sources)
            pass
    if not api_key and key_vault_name:
        try:
            vault_uri = f"https://{key_vault_name}.vault.azure.net"
            credential = DefaultAzureCredential()
            kv_client = SecretClient(vault_url=vault_uri, credential=credential)
            secret_bundle = kv_client.get_secret(key_vault_api_key_name)
            api_key = secret_bundle.value
        except Exception:
            pass

    return AzureOpenAIConfig(
        endpoint=endpoint.rstrip("/"),
        deployment=deployment,
        api_version=api_version,
        tenant_id=tenant_id,
        client_id=client_id,
        client_secret=client_secret,
        key_vault_name=key_vault_name,
        key_vault_secret_name=key_vault_secret_name,
        api_key=api_key,
        key_vault_api_key_name=key_vault_api_key_name,
    )


class AzureOpenAIClient:
    """Thin async client for Azure OpenAI Chat Completions using AAD tokens.

    - Uses DefaultAzureCredential chain (EnvironmentCredential preferred for SP).
    - Supports streaming via SSE-like 'data:' lines and yields parsed JSON chunks.
    """

    def __init__(self, config: AzureOpenAIConfig, session: Optional[aiohttp.ClientSession] = None):
        self._config = config
        # Prefer shared session from app.state if not provided
        if session is None:
            try:
                from main import app  # local import to avoid circulars at import time
                shared = getattr(app.state, "http_session", None)
                session = shared
            except Exception:
                pass
        self._session = session
        self._credential = DefaultAzureCredential()
        # Token provider callable that returns a fresh Bearer token string
        self._token_provider = get_bearer_token_provider(self._credential, COGNITIVE_SERVICES_SCOPE)

    @property
    def base_url(self) -> str:
        return f"{self._config.endpoint}/openai/deployments/{self._config.deployment}/chat/completions?api-version={self._config.api_version}"

    async def _get_headers(self) -> Dict[str, str]:
        # Prefer API key if provided; otherwise use AAD Bearer token
        if self._config.api_key:
            return {
                "api-key": self._config.api_key,
                "Content-Type": "application/json",
            }
        token = self._token_provider()
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

    async def chat(
        self,
        messages: List[Dict[str, Any]],
        temperature: float = 0.2,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[str] = None,
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {"messages": messages, "temperature": temperature}
        if tools:
            payload["tools"] = tools
        if tool_choice is not None:
            payload["tool_choice"] = tool_choice
        headers = await self._get_headers()
        close_session = False
        session = self._session
        if session is None:
            session = aiohttp.ClientSession()
            close_session = True
        try:
            async with session.post(self.base_url, headers=headers, json=payload, timeout=None) as resp:
                resp.raise_for_status()
                return await resp.json()
        finally:
            if close_session:
                await session.close()

    async def stream_chat(
        self,
        messages: List[Dict[str, Any]],
        temperature: float = 0.2,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[str] = None,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        payload: Dict[str, Any] = {"messages": messages, "temperature": temperature}
        if tools:
            payload["tools"] = tools
        if tool_choice is not None:
            payload["tool_choice"] = tool_choice
        # Enable server-sent events per Azure API (preferred over query param)
        payload["stream"] = True
        headers = await self._get_headers()
        # Hint streaming MIME type for some proxies
        headers["Accept"] = "text/event-stream"
        close_session = False
        session = self._session
        if session is None:
            session = aiohttp.ClientSession()
            close_session = True

        url = self.base_url
        try:
            async with session.post(url, headers=headers, json=payload, timeout=None) as resp:
                resp.raise_for_status()
                # Manual SSE parsing: accumulate text and split by newlines
                buffer = ""
                async for chunk_bytes in resp.content.iter_chunked(1024):
                    try:
                        buffer += chunk_bytes.decode("utf-8")
                    except Exception:
                        continue
                    while True:
                        nl = buffer.find("\n")
                        if nl == -1:
                            break
                        line = buffer[:nl].strip()
                        buffer = buffer[nl + 1 :]
                        if not line:
                            continue
                        if not line.startswith("data: "):
                            continue
                        data_part = line[len("data: "):].strip()
                        if data_part == "[DONE]":
                            return
                        try:
                            chunk = json.loads(data_part)
                            yield chunk
                        except Exception:
                            # Skip malformed lines
                            continue
        finally:
            if close_session:
                await session.close()


