# Fathom Backend Setup (Azure OpenAI + FastAPI)

This guide helps bring up the backend locally and prepare for workplace Azure. It covers environment variables, Azure resources, authentication, and smoke tests.

## What you are running
- FastAPI backend exposing:
  - LUSID task APIs at `/fathom/*`
  - Agent Playground at `/v1/playground/*` for chat (streams JSON events)
- Azure OpenAI via AAD (service principal) with Key Vault first, `.env` fallback
- Fixed model alias: `gpt-4o-azure` → uses your Azure OpenAI deployment (default `gpt-4o`)

## Prerequisites
- Python 3.11+ (3.13 OK)
- Virtualenv (or pyenv)
- Azure subscription (workplace will provide)
- A service principal (SP) and Key Vault access provided by enterprise team

## Directory
- Backend code: `backend/`
- This file: `docs/BACKEND-SETUP.md`
- Environment: repo-root `.env.local` (preferred), optionally `backend/.env`

## Install
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Environment variables
Place in repo-root `.env.local` (recommended). Backend automatically loads it.

Required (Azure OpenAI):
```bash
AZURE_TENANT_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
AZURE_CLIENT_ID=yyyyyyyy-yyyy-yyyy-yyyy-yyyyyyyyyyyy
AZURE_CLIENT_SECRET=YOUR_SP_SECRET            # optional if Key Vault provides it
AZURE_OPENAI_ENDPOINT=https://<your-aoai>.openai.azure.com
AZURE_OPENAI_DEPLOYMENT=gpt-4o               # or your workplace deployment name
AZURE_OPENAI_API_VERSION=2024-12-01-preview  # prefer this version
KEY_VAULT_NAME=<your-kv-name>                # optional, if using Key Vault
```
Optional fallback:
```bash
AZURE_OPENAI_API_KEY=<optional-api-key>
```

Notes:
- Single repo-root `.env.local` is loaded; you can also add `backend/.env` if needed.
- UI endpoint defaults to `http://localhost:8000` (no change required).

## Azure roles (enterprise)
Ask your enterprise team to provision:
- Azure OpenAI resource and a deployment (e.g., `gpt-4o`).
- Service Principal with role on AOAI: Cognitive Services OpenAI User.
- Key Vault with role for SP: Key Vault Secrets User.
- Secrets in Key Vault:
  - `AZURE-CLIENT-SECRET` → your SP client secret
  - (Optional) `AZURE-OPENAI-API-KEY` → direct API key fallback

## Corporate network notes
- If you have a proxy or TLS interception, set:
```bash
HTTPS_PROXY=https://<corp-proxy>
HTTP_PROXY=http://<corp-proxy>
REQUESTS_CA_BUNDLE=/path/to/corp-ca.pem
```
- Private endpoints/VNet are not required for local; keep public endpoints. Document later if needed.

## Run locally
```bash
cd backend
source venv/bin/activate
uvicorn main:app --reload --port 8000
```

## Smoke tests
- Health:
```bash
curl -s http://localhost:8000/health
```
- Playground status:
```bash
curl -s http://localhost:8000/v1/playground/status
```
- Agents list (fixed entry showing GPT‑4o):
```bash
curl -s http://localhost:8000/v1/playground/agents
```
- Chat run (newline-delimited JSON events):
```bash
curl -N -s -X POST http://localhost:8000/v1/playground/agents/fathom-agent/runs \
  -F message='Say hello briefly.'
```
Expected: `RunStarted` → `RunResponseContent` → `RunCompleted` with content.

## How Azure configuration is used
- File: `backend/fathom/clients/azure_openai_client.py`
  - Loads env vars; if `AZURE_CLIENT_SECRET` is not set and `KEY_VAULT_NAME` is set, it fetches the secret `AZURE-CLIENT-SECRET` from Key Vault using `DefaultAzureCredential`.
  - Prefers API key header if `AZURE_OPENAI_API_KEY` is present; otherwise uses AAD Bearer token.
  - Supports streaming (`stream_chat`) and non-stream fallback.
- File: `backend/fathom/routers/playground.py`
  - Exposes `/v1/playground/*` endpoints and streams newline-delimited JSON events.
  - Uses model alias `gpt-4o-azure` mapped to your deployment via env.
- File: `backend/fathom/config/models.yaml`
  - Records alias and default API version/deployment (env can override).

## Switching to workplace Azure
When your enterprise team provides outputs, update `.env.local`:
```bash
AZURE_TENANT_ID=<work-tenant>
AZURE_CLIENT_ID=<work-sp-client-id>
AZURE_OPENAI_ENDPOINT=https://<work-aoai>.openai.azure.com
AZURE_OPENAI_DEPLOYMENT=<work-deployment-name>
KEY_VAULT_NAME=<work-kv-name>
# Optionally remove AZURE_CLIENT_SECRET to force Key Vault retrieval
```
No code changes required. Restart backend to apply.

## LUSID configuration (recap)
- LUSID secrets can live in repo root as `secrets.json`, or use `FBN_SECRETS_PATH`/`LUSID_SECRETS_PATH` env.
- Backend loads and initialises a shared LUSID `ApiClientFactory` on startup.

## Troubleshooting
- 401/403 from AOAI: check RBAC roles, SP secret, and endpoint URL.
- 404: check `AZURE_OPENAI_DEPLOYMENT` matches Portal deployment name.
- 400: try `AZURE_OPENAI_API_VERSION=2024-12-01-preview`.
- Key Vault: ensure SP has Secrets User on the vault and correct secret names.
- Proxy: set `HTTPS_PROXY`, `HTTP_PROXY`, `REQUESTS_CA_BUNDLE` if your workplace intercepts TLS.

## Future
- Migrate secrets to Azure DevOps Library variables/secrets.
- Add private endpoints/VNet if enterprise requires.
- Add additional model aliases (e.g., Claude via Azure, direct OpenAI) behind the same gateway.
