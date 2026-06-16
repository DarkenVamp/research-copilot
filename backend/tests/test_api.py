"""End-to-end API tests against the real app (SQLite + mock mode)."""

from __future__ import annotations

import json
import time

from fastapi.testclient import TestClient

from app.main import app


def _parse_sse(body: str) -> list[dict[str, str]]:
    """Parse a buffered text/event-stream body into a list of {event, data}."""
    events: list[dict[str, str]] = []
    current: dict[str, str] = {}
    for line in body.splitlines():
        if line.startswith("event:"):
            current["event"] = line[len("event:") :].strip()
        elif line.startswith("data:"):
            current["data"] = line[len("data:") :].strip()
        elif line == "" and current:
            events.append(current)
            current = {}
    if current:
        events.append(current)
    return events


def _wait_until_done(client: TestClient, sid: str, timeout: float = 20.0) -> dict:
    deadline = time.time() + timeout
    detail = client.get(f"/api/sessions/{sid}").json()
    while detail["status"] not in ("completed", "failed") and time.time() < deadline:
        time.sleep(0.2)
        detail = client.get(f"/api/sessions/{sid}").json()
    return detail


def test_health_reports_mock_mode():
    with TestClient(app) as client:
        body = client.get("/health").json()
        assert body["status"] == "ok"
        assert body["mock_mode"] is True


def test_full_session_flow():
    with TestClient(app) as client:
        created = client.post(
            "/api/sessions",
            json={
                "company_name": "Acme Corp",
                "website": "https://acme.com",
                "objective": "Sell our CRM to their RevOps team",
            },
        )
        assert created.status_code == 201
        sid = created.json()["id"]

        run = client.post(f"/api/sessions/{sid}/run")
        assert run.status_code == 202

        detail = _wait_until_done(client, sid)
        assert detail["status"] == "completed"
        assert detail["report"] is not None
        assert len(detail["report"]["sources"]) > 0
        assert detail["report"]["discovery_questions"]

        # Workflow events were persisted, including the report node.
        events = client.get(f"/api/sessions/{sid}/events").json()
        nodes = [e["node"] for e in events]
        assert "planner" in nodes
        assert "report" in nodes

        # Follow-up chat streams the answer over SSE and persists both turns.
        chat = client.post(f"/api/sessions/{sid}/chat", json={"message": "Hello?"})
        assert chat.status_code == 200
        assert chat.headers["content-type"].startswith("text/event-stream")
        events = _parse_sse(chat.text)
        deltas = [e for e in events if e.get("event") == "delta"]
        done = [e for e in events if e.get("event") == "done"]
        assert deltas, "expected streamed delta events"
        assert done, "expected a terminal done event"
        # Concatenated deltas reproduce the persisted answer.
        streamed = "".join(json.loads(e["data"])["text"] for e in deltas)
        assert json.loads(done[0]["data"])["content"] == streamed

        messages = client.get(f"/api/sessions/{sid}/messages").json()
        assert len(messages) == 2


def test_validation_error_returns_422():
    with TestClient(app) as client:
        res = client.post("/api/sessions", json={"company_name": "", "objective": ""})
        assert res.status_code == 422
        assert res.json()["error"] == "validation_error"


def test_missing_session_returns_404():
    with TestClient(app) as client:
        res = client.get("/api/sessions/does-not-exist")
        assert res.status_code == 404


def test_chat_before_report_conflicts():
    with TestClient(app) as client:
        created = client.post(
            "/api/sessions",
            json={"company_name": "NoReport Inc", "objective": "test"},
        )
        sid = created.json()["id"]
        res = client.post(f"/api/sessions/{sid}/chat", json={"message": "hi"})
        assert res.status_code == 409
