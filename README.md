# AI Research Copilot

A production-minded AI research copilot that helps you prepare for a sales or
business meeting. Give it a company, a website, and your objective; it runs a
multi-step **LangGraph** workflow — plan → research → analyze → quality-check →
report — streams progress live, produces a structured briefing, and lets you
chat with the result.

> Stack: **React** (frontend) · **Python + FastAPI** (backend) · **LangGraph** (AI workflow) · **PostgreSQL** (persistence).

---

## Why this isn't "one LLM call behind an API"

The core is a real LangGraph workflow with five meaningful nodes, shared typed
state, **conditional routing with a bounded retry loop**, intermediate outputs
streamed to the UI, per-node failure handling, and **checkpoint-based
recoverability**.

```
        ┌─────────┐   ┌──────────┐   ┌──────────┐   ┌───────────────┐
START ─▶│ Planner │─▶ │ Research │─▶ │ Analysis │─▶ │ Quality Check │──┐
        └─────────┘   └──────────┘   └──────────┘   └───────────────┘  │
                           ▲                                            │ conditional
                           └────────────── gaps (retry) ───────────────┤
                                                                        ▼
                                                                  ┌──────────┐
                                                                  │  Report  │─▶ END
                                                                  └──────────┘
```

The **Quality Check** node is an LLM-as-judge that scores the analysis; if it
falls below a threshold and retries remain, the graph loops back to **Research**
to fill the specific gaps it identified, then re-analyzes. Every node transition
is checkpointed in Postgres keyed by `thread_id = session_id`, so an interrupted
run resumes from where it stopped.

See [`docs/architecture.md`](docs/architecture.md) for the full design and
[`docs/engineering-decisions.md`](docs/engineering-decisions.md) for the trade-offs.

---

## Features

- **Research sessions** — create with company, website, and objective.
- **Live workflow progress** — Server-Sent Events drive a stepper that shows each
  node's status, intermediate output, and how many times the retry loop ran.
- **Structured report** — Company Overview, Products & Services, Target Customers,
  Business Signals, Risks & Challenges, Suggested Discovery Questions, Suggested
  Outreach Strategy, Unknowns, and verified Sources.
- **Follow-up chat** — grounded strictly in the generated report.
- **Persistence** — sessions, reports, events, and chat in PostgreSQL; graph
  checkpoints for recoverability.
- **Real web research** — Tavily search + website fetch, with cited sources.
- **Mock mode** — with no API keys set, the whole app runs deterministically
  (great for grading, demos, and CI).

---

## Architecture

```
┌──────────────┐     HTTP / SSE      ┌─────────────────────────┐     ┌────────────┐
│  React (Vite)│ ──────────────────▶ │  FastAPI                │ ──▶ │ PostgreSQL │
│  - sessions  │ ◀────────────────── │  - session/workflow/chat│     │  app data  │
│  - stepper   │   report + events   │  - LangGraph engine     │     │  + graph   │
│  - chat      │                     │  - SSE pub/sub          │     │  checkpts  │
└──────────────┘                     └───────────┬─────────────┘     └────────────┘
                                                 │ tools
                                       ┌─────────▼──────────┐
                                       │ OpenAI · Tavily    │
                                       └────────────────────┘
```

---

## Quick start (Docker — recommended)

Requires Docker. Brings up Postgres, the API, and the web app:

```bash
# optional: real models + web search (otherwise mock mode)
export OPENAI_API_KEY=sk-...
export TAVILY_API_KEY=tvly-...

docker compose up --build
```

- Web app: http://localhost:5173
- API docs: http://localhost:8000/docs

## Quick start (local dev)

Run Postgres in Docker, then the backend and frontend on the host:

```bash
# 1. Postgres (PG18 + pgvector)
docker compose up -d postgres

# 2. Backend
cd backend
uv sync --extra dev
cp .env.example .env            # add OPENAI_API_KEY / TAVILY_API_KEY for real research
uv run uvicorn app.main:app --reload   # http://localhost:8000

# 3. Frontend (separate terminal)
cd frontend
npm install
npm run dev                            # http://localhost:5173 (proxies /api → :8000)
```

With no `OPENAI_API_KEY`, the workflow runs in **mock mode** end-to-end (it still
needs Postgres for persistence).

---

## Configuration

Backend settings (see [`backend/.env.example`](backend/.env.example)):

| Variable               | Default                                              | Notes |
|------------------------|------------------------------------------------------|-------|
| `OPENAI_API_KEY`       | _(empty)_                                            | Empty ⇒ mock mode |
| `OPENAI_MODEL`         | `gpt-4o`                                              | Synthesis nodes |
| `OPENAI_FAST_MODEL`    | `gpt-4o-mini`                                         | Routing / quality judge |
| `TAVILY_API_KEY`       | _(empty)_                                             | Empty ⇒ mock search |
| `DATABASE_URL`         | `postgresql+psycopg://copilot:copilot@localhost:5432/copilot` | psycopg3 driver; checkpointer DSN derived from it |
| `QUALITY_THRESHOLD`    | `0.7`                                                | Min quality score to finalize |
| `MAX_RESEARCH_RETRIES` | `2`                                                  | Retry-loop cap |
| `CORS_ORIGINS`         | `["http://localhost:5173", ...]`                     | JSON list |

---

## API

| Method | Path                              | Purpose |
|--------|-----------------------------------|---------|
| POST   | `/api/sessions`                   | Create a research session |
| GET    | `/api/sessions`                   | List sessions |
| GET    | `/api/sessions/{id}`              | Session detail (+ report) |
| POST   | `/api/sessions/{id}/run`          | Start the workflow |
| POST   | `/api/sessions/{id}/resume`       | Resume from last checkpoint |
| GET    | `/api/sessions/{id}/stream`       | **SSE** live progress |
| GET    | `/api/sessions/{id}/events`       | Persisted workflow events |
| POST   | `/api/sessions/{id}/chat`         | Ask a follow-up |
| GET    | `/api/sessions/{id}/messages`     | Chat history |
| GET    | `/health`                         | Health + mode |

Interactive docs at `/docs`.

---

## Project structure

```
backend/      FastAPI app, LangGraph workflow, persistence, tests
  app/graph/  state, nodes, router, builder, tools, prompts, mock, chat
  app/api/    sessions, workflow (run/resume/SSE/events), chat, health
  app/services/ engine (graph + checkpointer), workflow_runner, pubsub
frontend/     React + Vite + Tailwind SPA
docs/         architecture.md, engineering-decisions.md, product-improvements.md
docker-compose.yml
```

---

## Testing & quality

```bash
cd backend
uv run pytest        # graph + end-to-end API tests (spins up an ephemeral
                     # Postgres via testcontainers — needs a running Docker daemon)
uv run ruff check .  # lint

cd ../frontend
npm run typecheck    # strict TypeScript
npm run build
```

---

## Notes & limitations

- Postgres is the single datastore (app data + LangGraph checkpoints); Docker is
  required to run it locally and for the test suite (testcontainers).
- Mock mode is deterministic by design (the first quality check intentionally
  fails once to demonstrate the retry loop).
- Further productionization ideas are in
  [`docs/product-improvements.md`](docs/product-improvements.md).
