"""Conditional-edge functions."""

from __future__ import annotations

from app.config import settings
from app.graph.state import NODE_REPORT, NODE_RESEARCH, ResearchState


def route_after_quality(state: ResearchState) -> str:
    """Route to report once quality passes or retries are exhausted, else re-research."""
    quality = state.get("quality") or {}
    retries = state.get("retries", 0)

    if quality.get("passed"):
        return NODE_REPORT
    if retries >= settings.max_research_retries:
        return NODE_REPORT
    return NODE_RESEARCH
