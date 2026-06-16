# Architecture

## Overview

The system has three tiers: a React SPA, a FastAPI backend that hosts the
LangGraph workflow, and PostgreSQL for both application data and graph
checkpoints. External capability comes from OpenAI (LLM) and Tavily (web search).

```
                                      +--------------------+
+------------------+                  | FastAPI            |      +-------------+
| React (Vite) SPA |    HTTP + SSE    |                    |      | PostgreSQL  |
|                  |  --------------> | sessions           | ---->|             |
| session create   |  <-------------- | workflow (run/SSE) |      | app data    |
| history / detail |  report+events   | chat (SSE)         |      | + LangGraph |
| live stepper     |                  | LangGraph engine   |      | checkpoints |
| follow-up chat   |                  | SSE pub/sub        |      +-------------+
+------------------+                  +--------------------+
                                                 |
                                                 v  tools
                                      +-----------------+
                                      | OpenAI / Tavily |
                                      +-----------------+
```

## Request / data flow

1. **Create session** — `POST /api/sessions` persists a `ResearchSession`
   (`status=created`).
2. **Run** — `POST /api/sessions/{id}/run` schedules `run_workflow` as a
   background task and returns immediately (202).
3. **Execute** — `workflow_runner` streams `graph.astream(stream_mode="updates")`.
   For each node update it (a) persists a `WorkflowEvent` and (b) publishes it to
   an in-process **pub/sub**.
4. **Observe** — the UI opens `GET /api/sessions/{id}/stream` (SSE). The endpoint
   replays already-persisted events (catch-up), then tails live ones until a
   terminal event — so it works whether the run is in-flight or already done.
5. **Report** — when the `report` node emits, the runner stores the structured
   report and marks the session `completed`.
6. **Chat** — `POST /api/sessions/{id}/chat` answers follow-ups grounded only in
   the stored report, **streaming the answer token-by-token over SSE** (`delta`
   events, then a terminal `done`); both turns are persisted.

## The LangGraph workflow

```
                                            gaps (retry)
                                +-----------------------------------+
                                |                                   |
                                v                                   |         pass
          +---------+     +----------+     +----------+     +---------------+     +--------+
START --> | Planner | --> | Research | --> | Analysis | --> | Quality Check | --> | Report | --> END
          +---------+     +----------+     +----------+     +---------------+     +--------+
```

### Shared state (`app/graph/state.py`)

A single `ResearchState` TypedDict flows through every node. List fields
(`findings`, `sources`, `errors`) use the `add` reducer so the research retry
loop **accumulates** evidence instead of overwriting it; scalar/dict fields
(`plan`, `analysis`, `quality`, `report`, `retries`) overwrite.

### Nodes (`app/graph/nodes/`)

| Node | Responsibility | Intermediate output |
|------|----------------|---------------------|
| **planner** | Decompose the objective into focus areas + search queries | `ResearchPlan` |
| **research** | Tavily search per query + website fetch; on retry, target only the identified gaps | appends `findings`, `sources` |
| **analysis** | Synthesize findings into a structured analysis; record `unknowns` | `Analysis` |
| **quality_check** | LLM-as-judge scores grounding/completeness; pass/fail vs. threshold | `QualityAssessment` |
| **report** | Assemble the final briefing; attach verified sources | `ResearchReport` |

### Conditional routing (`app/graph/router.py`)

After `quality_check`, `route_after_quality` returns:
- `report` if the assessment passed, **or** retries hit `MAX_RESEARCH_RETRIES`;
- `research` otherwise — looping back to gather the specific gaps the judge named.

### Failure handling & recoverability

- Each node wraps its LLM/tool work in `try/except`, appends to `state.errors`,
  and **degrades** to a deterministic fallback rather than crashing the run.
- The graph is compiled with an `AsyncPostgresSaver` checkpointer. Every
  super-step is persisted under `thread_id = session_id`. `POST /resume` calls
  the graph with `None` input, which continues from the last checkpoint.

## Persistence (`app/db/`)

- **Application data** via async SQLAlchemy (psycopg3 driver): `sessions`,
  `reports`, `workflow_events`, `chat_messages`. JSON payloads use `JSONB`. The
  schema is managed by **Alembic** (applied on startup; `AsyncPostgresSaver`
  checkpoint tables are excluded from autogenerate via `include_name`).
- **Graph checkpoints** in a separate set of LangGraph-managed tables, on a
  dedicated psycopg connection pool.
- **One driver: psycopg 3** (async, non-blocking) for both the SQLAlchemy engine
  and the checkpointer — the checkpointer is psycopg-only, so this avoids a second
  Postgres driver (asyncpg). See `engineering-decisions.md` §3.
- Single datastore: Postgres (PG18 + pgvector) everywhere — production, local
  dev (`docker compose up postgres`), and tests (an ephemeral Postgres via
  testcontainers). No second dialect to keep in sync.

## Streaming design

A lightweight in-process `PubSub` (`app/services/pubsub.py`) fans workflow events
out to SSE subscribers. The runner is the sole publisher; the SSE endpoint is the
subscriber. A single-process assumption keeps it simple; scaling horizontally
would swap the implementation for Redis pub/sub or Postgres `LISTEN/NOTIFY`
behind the same interface, with no change to the runner or endpoint.

Both SSE endpoints (workflow progress and chat) do their DB reads in a
**short-lived session that is released before the long-lived stream begins** —
the streaming loop then reads only from the in-process queue. So an open SSE
connection never pins a pooled DB connection for the lifetime of the stream,
which would otherwise let a handful of idle viewers exhaust the connection pool.

## Configuration, logging, errors

- **Config** — one typed `Settings` (pydantic-settings); no scattered `os.getenv`.
- **Logging** — structured JSON to stdout in deployed environments (via
  `python-json-logger`), and plain human-readable lines when `ENVIRONMENT=local`;
  a middleware logs method/path/status/duration per request.
- **Errors** — exception handlers return a consistent `{error, detail}` envelope
  for HTTP, validation, and unhandled errors.

## Mock mode

When `OPENAI_API_KEY` is absent, nodes use deterministic builders
(`app/graph/mock.py`) and Tavily falls back to canned results. The first quality
check intentionally fails once so the retry loop is always exercised. This makes
the entire system runnable and testable with no external dependencies.
