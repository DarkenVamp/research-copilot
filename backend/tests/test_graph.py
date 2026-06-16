"""Tests for the LangGraph workflow (mock mode, in-memory checkpointer)."""

from __future__ import annotations

import pytest
from langgraph.checkpoint.memory import MemorySaver

from app.config import settings
from app.graph.builder import build_graph
from app.graph.router import route_after_quality
from app.graph.state import NODE_REPORT, NODE_RESEARCH
from app.graph.util import dedupe_sources, format_findings


@pytest.fixture
def graph():
    return build_graph(MemorySaver())


def _initial_state():
    return {
        "session_id": "test-1",
        "company_name": "Acme Corp",
        "website": "https://acme.com",
        "objective": "sell our CRM platform",
        "findings": [],
        "sources": [],
        "errors": [],
        "retries": 0,
    }


async def test_workflow_runs_full_pipeline_with_retry_loop(graph):
    cfg = {"configurable": {"thread_id": "test-1"}}
    visited: list[str] = []
    async for chunk in graph.astream(_initial_state(), cfg, stream_mode="updates"):
        visited.extend(chunk.keys())

    # Pipeline starts at planner and ends at report.
    assert visited[0] == "planner"
    assert visited[-1] == "report"
    # The conditional loop ran research at least twice (quality failed once).
    assert visited.count("research") >= 2

    state = (await graph.aget_state(cfg)).values
    assert state["retries"] == 1
    assert state["quality"]["passed"] is True

    report = state["report"]
    for key in (
        "company_overview",
        "products_and_services",
        "target_customers",
        "business_signals",
        "risks_and_challenges",
        "discovery_questions",
        "outreach_strategy",
        "unknowns",
        "sources",
    ):
        assert key in report
    assert len(report["sources"]) > 0


def test_router_passes_to_report_when_quality_ok():
    assert route_after_quality({"quality": {"passed": True}, "retries": 0}) == NODE_REPORT


def test_router_loops_back_when_quality_fails_with_retries_left():
    assert (
        route_after_quality({"quality": {"passed": False}, "retries": 0}) == NODE_RESEARCH
    )


def test_router_stops_after_max_retries():
    state = {"quality": {"passed": False}, "retries": settings.max_research_retries}
    assert route_after_quality(state) == NODE_REPORT


def test_dedupe_sources_removes_duplicate_urls():
    out = dedupe_sources(
        [
            {"title": "a", "url": "https://x.com"},
            {"title": "b", "url": "https://x.com"},
            {"title": "c", "url": "https://y.com"},
            {"title": "d", "url": ""},
        ],
    )
    assert [s["url"] for s in out] == ["https://x.com", "https://y.com"]


def test_format_findings_handles_empty():
    assert "no findings" in format_findings([])
