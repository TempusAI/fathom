
Spec.md — Fathom (LUSID Data-Quality Agent with Agno Agent UI)

Last updated: 06 Sep 2025 (AEST). British English.
Scope: MVP with UI, read-only investigation of LUSID Aggregation Errors. Tools for information gathering only; resolution tools will follow.

⸻

0) Purpose

Build Fathom, a UI-driven agent that:
	1.	Shows Workflow Tasks (incl. nested structures) in Agno’s Agent UI,
	2.	Lets a user filter by date, select one or more tasks (chips added to composer),
	3.	Runs LUSID Luminesce (SQL) info-gathering tools via Honeycomb /honeycomb/api/Sql/json and Workflow GET APIs,
	4.	Reasons over results using a pluggable model gateway (Claude Azure by default; OpenAI/GPT-5 & router optional),
	5.	Returns a markdown summary with evidence + provenance, and
	6.	Writes audit to Azure storage (sessions/history + audit entries).

UI framework: Agno Agent UI (Next.js, TypeScript). Backend: Agno Playground (FastAPI) hosting the Fathom agent and tools.  ￼

⸻

1) Goals & Non-Goals

Goals (MVP)
	•	Task explorer panel: hierarchical list (Ultimate Parent → Task → Children), expandable, with date filter (by asAtLastTransition).
	•	Task chips in composer: click a row → chip appears (with ✕ to remove).
	•	“Investigate” interaction: User asks “Investigate” (or similar); Fathom ingests selected task(s) + fields as context; runs tools; returns markdown findings with sample rows and query IDs.
	•	Model switching: default Claude Azure; aliases for o4-azure, gpt5-openai, optional router-litellm.
	•	Azure storage for sessions/history + audit (no local SQLite).
	•	Read-only LUSID access (Workflow GET, SQL JSON).

Non-Goals (MVP)
	•	No task updates or batch updates (write ops deferred).
	•	No triage scoring or auto-resolution (deferred).
	•	No rate-limit/guardrail enforcement (you requested none for personal-machine MVP).

⸻

2) High-Level Architecture

Agent UI (Next.js)    ───►  Playground (FastAPI, Python)
(task panel + chat)            ├─ Fathom Agent (reasoner)
                                ├─ LUSID Auth (ApiClientFactory + RefreshingToken)
                                ├─ Workflow Client (GET task/list/history)
                                ├─ Honeycomb SQL Client (/honeycomb/api/Sql/json)
                                ├─ Tools (sysfields, instrument, quotes, holdings, txn)
                                ├─ Model Gateway (Claude Azure, OpenAI, router)
                                └─ Azure Storage Adapters (sessions/history + audit)

	•	Why this shape? Agno’s UI natively points at a playground server for agents; keeping tools/credentials on the backend is cleaner and enterprise-ready.  ￼

⸻

3) Environments & Config

LUSID (demo tenant, MVP)
	•	Workflow API base: https://simpleflow.lusid.com/workflow/api
	•	Honeycomb SQL JSON: https://simpleflow.lusid.com/honeycomb/api/Sql/json
	•	Auth: lusid.utilities.ApiClientFactory(token=RefreshingToken()) using FBN_SECRETS_PATH (Okta pattern you use).
	•	Bearer reuse: forward the same access token to both Workflow and Honeycomb requests (established at AustralianSuper).

Models (model alias → provider)
	•	Default claude-azure; enabled: claude-azure, o4-azure, gpt5-openai, router-litellm.
	•	Temperature: we choose sensible default 0.2; token limits set high (up to model cap).
	•	Config file: config/models.yaml.

Azure storage
	•	Sessions/history: Azure Table FathomSessions (or Cosmos Table API), plus Azure Blob FathomMessages (optional) for long transcripts.
	•	Audit: Azure Table FathomAudit (per-event rows).

⸻

4) UI/UX (Agent UI)

4.1 Layout
	•	Left panel: Tasks with:
	•	Date filter (calendar dropdown → filters by asAtLastTransition),
	•	Search (free-text across taskDefinitionDisplayName, state, fields.name),
	•	Hierarchy: rows with chevrons to expand Ultimate Parent → Task → Children,
	•	Inline details: state, counts, last transition timestamp.
	•	Main chat: standard Agent UI thread.
	•	Composer: shows task chips for each selection (click to add; ✕ to remove).

4.2 Interaction pattern
	1.	User chooses day (optional), expands hierarchy, clicks task(s) → chips added.
	2.	User types: “Investigate” (or any question).
	3.	Backend receives chips → fetches full Task(s) → maps fields → runs tools → reasons → returns markdown with:
	•	suspected error type,
	•	root cause summary,
	•	evidence (query IDs + compact sample rows),
	•	suggested next steps (read-only recommendations),
	•	model alias used + timings.

Agent UI and Playground coupling is standard; you will point the UI endpoint to your local Playground (e.g., http://localhost:7777).  ￼

⸻

5) Backend (Playground) — Fathom Agent

5.1 Agent Registration (mini snippet)

# playground.py (sketch)
from agno.playground import Playground
from fathom.agent import build_fathom_agent  # you implement
from fathom.storage.azure import AzureSessionStore, AzureAuditSink

agent = build_fathom_agent(
    model_alias="claude-azure",
    session_store=AzureSessionStore(...),
    audit_sink=AzureAuditSink(...)
)
playground = Playground(agents=[agent])
app = playground.get_app()

5.2 Authentication (Okta via SDK)

from lusid.utilities import ApiClientFactory
from lusidjam import RefreshingToken

api_factory = ApiClientFactory(token=RefreshingToken(), api_secrets_filename=os.getenv("FBN_SECRETS_PATH"), app_name="Fathom")
access_token = api_factory.api_client.configuration.access_token  # forward to Workflow/Honeycomb

For Luminesce SQL, LUSID’s SqlExecution API accepts SQL in JSON. Your Honeycomb JSON endpoint is the target for this MVP; Luminesce SQL semantics documented by FINBOURNE.  ￼

⸻

6) Tooling (Information-Gathering Set)

All tools are read-only and call either Workflow GET endpoints or Honeycomb SQL JSON.

6.1 Workflow tools
	•	wf_get_task(id) → GET /workflow/api/tasks/{id} → returns the Task body.
	•	wf_list_tasks({from,to,state,scope,search,page}) → GET /workflow/api/tasks with query params → returns paged list.
	•	wf_get_task_history(id) → GET /workflow/api/tasks/{id}/history → returns event timeline.

6.2 Luminesce (via Honeycomb SQL JSON)
	•	get_sysfields(table_names[])
	•	SQL: SELECT TableName, FieldName, DataType, FieldType, IsPrimaryKey, Description FROM Sys.Field WHERE TableName IN @table_names ORDER BY TableName, FieldName;
	•	Use to validate available fields at runtime for target providers.
	•	get_instrument(identifiers[])
	•	Resolve LusidInstrumentId + display IDs.
	•	get_quotes(instrument_id_type, instrument_id, from, to)
	•	Returns recent quotes window for staleness/missing-price checks.
	•	get_holdings(scope, portfolio_code, [from], [to])
	•	If [from,to] omitted, fetch latest position (okay for MVP).
	•	get_txn(scope, portfolio_code, lusid_instrument_id, from, to)
	•	Returns recent transactions for sub-holding mismatch patterns.

We’ll keep parameters minimal and refine with get_sysfields feedback. If long-running queries arise, consider LUSID’s SqlBackground API in a later slice.  ￼

6.3 SQL JSON (mini snippet)

def execute_sql_json(sql: str, params: dict | None = None, query_name: str = "Fathom.Query"):
    url = f"{HONEYCOMB_BASE}/api/Sql/json"
    headers = {"Authorization": f"Bearer {access_token}"}
    payload = {"Sql": sql, "QueryName": query_name, "Parameters": params or {}}
    return httpx.post(url, json=payload, headers=headers, timeout=None).json()


⸻

7) Reasoning & Model Switching
	•	Model Gateway with aliases:
	•	claude-azure (default), o4-azure, gpt5-openai, router-litellm.
	•	Config in config/models.yaml; choose temperature=0.2; high token limits (per provider caps).
	•	The agent composes a compact JSON payload for the model (task meta + heuristic signals + sample rows) and expects validated JSON back (suspected error type, summary, evidence, next steps, confidence).

Agno provides model wrappers; we keep an internal gateway to abstract Azure Anthropic vs Azure OpenAI vs router, set via UI or env.  ￼

⸻

8) Data Model & Mapping
	•	Task field mapping (config/task_field_map.yaml) translates fields[].name to semantic keys Fathom expects:
	•	portfolio_scope, portfolio_code, valuation_date, instrument_id_type, instrument_id_value, etc.
	•	If fields are missing, optionally parse from taskDefinitionDisplayName/description.

⸻

9) Storage (Azure)

You asked to avoid local SQLite; we’ll implement Azure storage for both agent sessions and audit.
	•	Sessions/History: Azure Table FathomSessions with:
	•	PartitionKey: SessionDate (YYYYMMDD)
	•	RowKey: session_id (uuid)
	•	Columns: UserId?, ModelAlias, MessagesBlobUri?, CreatedAt, UpdatedAt
	•	Messages (optional): Azure Blob fathom-messages/<session_id>.jsonl
	•	Audit: Azure Table FathomAudit using the JSON schema below (Section 12 in the previous version; we’ll reuse the same fields here).
	•	PartitionKey: YYYYMMDD, RowKey: run_id (+ suffix for tool/model events)

Agent UI itself stores settings locally by default; our Playground owns the canonical session/audit story in Azure to align with your enterprise expectations.  ￼

⸻

10) UX Contracts (frontend ↔ backend)

10.1 Endpoints (Playground)
	•	GET /fathom/tasks?date=YYYY-MM-DD&state=open|* → hierarchical list for UI panel
	•	GET /fathom/tasks/{id} → full Task for a clicked row
	•	POST /fathom/investigate → body: { taskIds: string[], question: string, modelAlias?: string }
	•	Returns: { markdown: string, modelAlias: string, runId: string }

10.2 Message protocol
	•	When user submits with chips, UI calls POST /fathom/investigate with chip IDs + message.
	•	Backend returns the rendered markdown for the chat transcript, plus model alias and run id.

⸻

11) Output (Agent Response)

Sections (markdown):
	1.	Summary (1–3 lines)
	2.	Suspected error type (enum) + confidence
	3.	Evidence (query IDs, row counts, compact samples)
	4.	Suggested next steps (read-only)
	5.	Provenance (model alias, tokens if available, run id, durations)

⸻

12) Audit (Azure)
	•	Persist per-run records: run, tool_call, model_io, error.
	•	Fields: TaskId, PortfolioScope, PortfolioCode, LusidInstrumentId?, ValuationDate?, ModelAlias, QueryId, RowCount, DurationMs, CreatedAt, Confidence?, etc.
	•	We’ll reuse the prior audit JSON Schema (draft 2020-12).
	•	ROI line (later): once enough samples exist, compute P × V − (1 − P) × C > $ per model.

⸻

13) Implementation Plan (phased)

M1 — Plumbing & Scaffolding
	•	Playground app skeleton; envs for LUSID/Okta, Azure, models.
	•	Azure storage adapters: session & audit (minimal CRUD).
	•	Workflow client (GET list/task/history); Honeycomb SQL client.

Acceptance: Playground serves; /fathom/tasks returns demo data; Azure Tables created.

⸻

M2 — Tools & Mapping
	•	Implement sysfields/instrument/quotes/holdings/txn.
	•	Add config/task_field_map.yaml; parse Task → context.
	•	Prepare compact evidence payloads (sample up to 10 rows/section).

Acceptance: Tool calls return rows on demo tenant; sysfields validates columns.

⸻

M3 — Reasoning & Model Switching
	•	Implement Model Gateway with aliases and models.yaml.
	•	Azure Anthropic (Claude) default; Azure OpenAI and router optional.
	•	JSON schema validated result (suspected error, summary, evidence, next steps, confidence).

Acceptance: POST /fathom/investigate returns well-formed markdown and audit entries with ModelAlias.

⸻

M4 — Agent UI Integration
	•	Task panel with hierarchy & date filter.
	•	Chips in composer; ✕ removal.
	•	Wire UI → Playground endpoints; render markdown replies.

Acceptance: “See task list, filter by date, add chip, ask ‘Investigate’, agent runs tools, returns markdown with evidence, audit entries recorded, model alias shown in UI.”

⸻

M5 — Polish
	•	Loading states, basic error toasts.
	•	Minimal docs (README.md) and .env.example.
	•	Optional: settings menu for model alias override.

Acceptance: Happy path demo recorded (screen capture) end-to-end.

⸻

14) Minimal Snippets (for guidance only)

Playground serve

python playground.py  # exposes http://localhost:7777

Agno Agent build (sketch)

def build_fathom_agent(model_alias: str, session_store, audit_sink):
    return Agent(
        name="Fathom",
        model=resolve_model_from_alias(model_alias),
        tools=[WfGetTask(), WfListTasks(), WfGetTaskHistory(),
               GetSysFields(), GetInstrument(), GetQuotes(), GetHoldings(), GetTxn()],
        storage=session_store,
        instructions=["Investigate LUSID aggregation errors. Use tools. Return markdown with evidence."],
        markdown=True
    )

Investigate orchestration (very small outline)

def investigate(task_ids: list[str], question: str, model_alias: str):
    tasks = [wf_get_task(tid) for tid in task_ids]
    ctx = normalize_tasks(tasks, task_field_map)
    ev = gather_evidence(ctx)  # calls tools
    result = reason(model_alias, ctx, ev)  # JSON → markdown
    audit_sink.write_run(...); return result


⸻

15) Open Items (later slices)
	•	Resolution tool set: Workflow $update, tasks/{id} PATCH, and any safe LUSID remediation runners (behind confirm prompts).
	•	Triage: per-type priority rules (NAV impact, age, count of portfolios).
	•	SqlBackground for long-running queries.  ￼
	•	Governance: rate limits, timeouts, redactors (on by default when you move inside the fund).

⸻

16) Setup Notes
	•	Agent UI: npx create-agent-ui@latest → run at http://localhost:3000, point to Playground endpoint (e.g., http://localhost:7777).  ￼
	•	Playground: follow Agno Playground docs; register Fathom agent(s).  ￼
	•	Luminesce SQL: general SqlExecution documentation for syntax and JSON formats (your Honeycomb JSON endpoint is the transport).  ￼

⸻

17) Acceptance Criteria (recap)
	•	Task list displays with hierarchy and date filter.
	•	Clicking rows adds chips to the composer; ✕ removes.
	•	“Investigate” runs selected tasks end-to-end and returns markdown summary with evidence (query IDs + sample rows).
	•	Audit entries appear in Azure with model alias and timings.
	•	UI shows model alias used for each response.