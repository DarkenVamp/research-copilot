# Research Copilot — Backend

FastAPI + LangGraph backend for the AI Research Copilot. See the
[root README](../README.md) for full setup and the project overview, and
[`docs/architecture.md`](../docs/architecture.md) for the design.

## Quick start

```bash
uv sync --extra dev
cp .env.example .env          # optionally add OPENAI_API_KEY / TAVILY_API_KEY
uv run uvicorn app.main:app --reload
```

Postgres must be reachable at `DATABASE_URL` (see root `docker-compose.yml`).
With no `OPENAI_API_KEY` set the workflow runs in deterministic **mock mode**.
