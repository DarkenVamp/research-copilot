# Engineering Decisions

## 1. LangGraph with a Postgres checkpointer (not a hand-rolled pipeline)

**Decision.** Model the research process as a compiled LangGraph `StateGraph`
with a shared typed state and a Postgres checkpointer keyed by `session_id`.

**Alternatives considered.**
- A plain async function chaining LLM calls.
- A task queue (Celery/RQ) orchestrating discrete steps.

**Trade-offs.** LangGraph adds a dependency and a learning curve, and its
checkpoint tables are an opaque schema we don't own. In return we get
conditional routing, a clean retry loop, and **recoverability for free**: an
interrupted run resumes from its last super-step instead of restarting. A
hand-rolled chain would have meant re-implementing checkpointing and routing; a
task queue would have added infra and made the "shared state" story messier. For
a workflow whose value *is* its multi-step structure, the graph framework earns
its keep — and it's exactly what the assignment asks to be assessed on.

## 2. Server-Sent Events for live progress (not WebSockets or polling)

**Decision.** Stream node-level progress over SSE; the backend persists each
event and republishes it through an in-process pub/sub. The SSE endpoint replays
persisted events on connect, then tails live ones.

**Alternatives considered.**
- WebSockets.
- Client polling of `GET /events`.

**Trade-offs.** Progress is strictly server→client and append-only, so SSE is the
right-sized tool — it's plain HTTP, auto-reconnects, and needs no extra protocol
or library on the client (`EventSource`). WebSockets would add bidirectional
machinery we don't need; polling is simpler still but trades latency and wasted
requests. The cost of SSE here is the single-process pub/sub assumption (see
risks), which is acceptable for the assignment and has a clear scale-out path.

## 3. PostgreSQL as the default, with a SQLite fallback for dev/test

**Decision.** Postgres is the production default (app data + graph checkpoints,
via docker-compose). The persistence layer is dialect-portable, so a
`sqlite+aiosqlite` `DATABASE_URL` runs the entire stack with zero setup.

**Alternatives considered.**
- Postgres only.
- SQLite only.

**Trade-offs.** Supporting two dialects cost a little care — a `JSONB`/`JSON`
typed variant and a portable integer-autoincrement ordering key instead of a
Postgres sequence. The payoff is large: the same code runs in production on
Postgres and runs in CI, tests, and a laptop with no database server at all.
Postgres alone would block local runs without Docker; SQLite alone would be a
weak "production" story and lose `JSONB`/concurrency.

---

## Top technical-debt items

1. **`create_all` instead of migrations.** Schema is created on startup. Fine for
   a demo; production needs Alembic migrations for safe evolution.
2. **In-process pub/sub.** Progress streaming is bound to a single backend
   process; multiple workers wouldn't share events.
3. **Background tasks via `asyncio.create_task`.** Runs are fire-and-forget in the
   web process — no durable queue, no retries on process crash (a checkpoint
   exists, but nothing automatically resumes it).
4. **Whole-report context for chat.** The follow-up chat stuffs the full report
   into the prompt instead of retrieval; fine now, won't scale to long histories.
5. **Coarse cost/latency controls.** No per-session token budgets, caching of
   search results, or rate-limit backoff beyond the SDK defaults.

## Biggest technical risk

**External dependency variance — LLM/search latency, cost, and reliability.**
The product's quality and run time hinge on third-party calls whose latency and
output shape vary, and whose failures or rate limits surface mid-workflow.
Mitigations already in place: per-node failure handling with deterministic
fallbacks, a bounded retry loop, structured-output schemas, and a deterministic
mock mode. What's still missing: result caching, circuit breaking, and explicit
token/cost budgets per run.

## What I'd do with two more weeks

- **Durable execution:** move runs to a real queue (e.g. Celery/Arq) with a
  worker that auto-resumes interrupted graphs from their checkpoints.
- **Migrations & multi-tenancy:** Alembic; users/auth; per-user session scoping.
- **Evaluation harness:** golden companies + an LLM-graded rubric to measure
  report quality across prompt/model changes (and gate deploys on it).
- **Cost & caching:** cache Tavily/website fetches, add per-run token budgets,
  and surface cost/latency per session in the UI.
- **Streaming tokens & richer progress:** stream the report as it's written and
  show live source counts; collapse the retry loop into a clearer timeline.
- **Scale-out streaming:** replace in-process pub/sub with Redis or Postgres
  `LISTEN/NOTIFY` so multiple backend replicas can serve SSE.
- **Hardening:** request auth, rate limiting, retries with backoff/circuit
  breakers, and end-to-end tracing.
