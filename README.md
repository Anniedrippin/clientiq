# ClientIQ — AI Consulting Analytics Copilot

An AI-powered analytics platform that connects to multiple enterprise data
sources, runs a LangGraph agent pipeline to find root causes, and produces
executive-ready, fully-cited recommendations — with a live Agent Trace View
so every step is auditable.

## Architecture

```
frontend/   React + Vite SPA (dashboard, chat, trace view, citations, export)
backend/    FastAPI + LangGraph + ChromaDB + Groq
  app/core/         config, JWT security, the shared logging template
  app/mcp/           6 MCP-style connectors (Postgres, CSV, Slack, Jira, Salesforce, Sheets)
  app/agents/        LangGraph state + 12 nodes + graph wiring
  app/services/      Groq LLM client, ChromaDB vector store, PDF export, trace cache
  app/api/           auth / analysis / kpi / trace / export routes
```

## One consistent logging template, everywhere

Every module — API routes, MCP connectors, LangGraph nodes, the LLM client,
the vector store, PDF export, and even the React frontend — logs through the
exact same shape:

```json
{
  "timestamp": "2026-07-22T05:41:00.791Z",
  "level": "INFO",
  "service": "clientiq-backend",
  "module": "app.mcp.base",
  "event": "mcp_tool_call_completed",
  "request_id": "5fee52fbe33446e9",
  "duration_ms": 0.5,
  "status": "success",
  "record_count": 1
}
```

Backend: `app/core/logging_config.py` → `get_logger()` + `log_event()`.
Frontend: `src/api/logger.js` → `logEvent()`, deliberately mirroring the same
fields so the whole system reads as one audit trail. A single `request_id`
is generated per HTTP request and threaded through every log line and every
Agent Trace step for that request, so you can grep `clientiq.log` for one
`request_id` and see the entire story: which MCP tools were called, what
queries ran, what the LLM did, and what was returned to the user.

## Quick start

### Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # optionally add a GROQ_API_KEY
uvicorn app.main:app --reload --port 8000
```

Without a `GROQ_API_KEY`, the app runs in deterministic offline-reasoning
mode — the LangGraph pipeline still executes all 12 nodes and every MCP
connector, it just skips the actual Groq call and uses a rule-based
fallback for root causes / recommendations / summary. This is logged
explicitly (`llm_reasoning_skipped_no_api_key`) so it's never silent.

Demo logins:
- `analyst@clientiq.ai` / `Analyst123!`
- `partner@clientiq.ai` / `Partner123!`

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Visit `http://localhost:5173`. Vite proxies `/api/*` to `http://localhost:8000`.

## What's mocked vs. real

This build is fully self-contained so it runs with zero external
infrastructure and no API keys:

| Component | This build | Swap in for production |
|---|---|---|
| Postgres / Slack / Jira / Salesforce / Google Sheets MCP connectors | Seeded, deterministic mock data behind the exact same `call_tool(tool, **kwargs)` interface a real MCP client would use | Point `BaseMCPConnector._run()` at a real MCP server session (`mcp` python SDK) using the DSNs/workspace IDs already in `app/core/config.py` |
| ChromaDB embeddings | Dependency-free hashing embedding function (`HashingEmbeddingFunction`) — no network call, works in firewalled environments | Swap for a hosted embedding model if you want stronger semantic recall |
| Groq LLM | Real call to `api.groq.com` if `GROQ_API_KEY` is set, else deterministic fallback | Just set `GROQ_API_KEY` in `.env` |
| Analysis/trace cache | In-process dict (`services/trace_service.py`) | Swap for Redis/Postgres for multi-instance deployments |

## Key endpoints

- `POST /api/auth/login` — JWT login
- `POST /api/analysis/ask` — runs the full LangGraph pipeline, returns
  executive summary, root causes, recommendations, citations, and the
  full agent trace
- `GET  /api/kpi?region=North` — dashboard KPI cards + anomaly detection
- `GET  /api/trace/{request_id}` — the Agent Trace View data
- `GET  /api/export/{request_id}/pdf` — executive PDF export

## Example flow

Ask: *"Why did revenue drop by 12% in the North region last quarter?"*

The LangGraph pipeline: queries Postgres for revenue, Postgres+Salesforce
for churn, a CSV upload for inventory stockouts, Slack for customer
complaints, Jira for delivery-delay tickets, Google Sheets for a recovery
forecast, and ChromaDB for prior quarterly reports — then reasons over all
of it to produce a primary cause (inventory stockouts), a secondary cause
(delivery delays → churn), a cited executive summary, and a prioritized
recommendation with an estimated dollar impact. Every one of those steps
shows up, in order, with timing and status, in the Agent Trace View.
