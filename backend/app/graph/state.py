"""Shared graph state.

Every node reads from and writes to this single typed object. List fields use the
`add` reducer so nodes can append (findings/sources accumulate across the
research retry loop) without clobbering earlier values; scalar/dict fields use the
default overwrite semantics.
"""

from __future__ import annotations

from operator import add
from typing import Annotated, TypedDict

# Canonical node names — referenced by the builder, router, and workflow runner.
NODE_PLANNER = "planner"
NODE_RESEARCH = "research"
NODE_ANALYSIS = "analysis"
NODE_QUALITY = "quality_check"
NODE_REPORT = "report"

NODE_ORDER = [NODE_PLANNER, NODE_RESEARCH, NODE_ANALYSIS, NODE_QUALITY, NODE_REPORT]


class ResearchState(TypedDict, total=False):
    # Inputs
    session_id: str
    company_name: str
    website: str | None
    objective: str

    # Intermediate outputs
    plan: dict | None
    findings: Annotated[list[dict], add]
    sources: Annotated[list[dict], add]
    analysis: dict | None
    quality: dict | None
    report: dict | None

    # Control / bookkeeping
    retries: int
    errors: Annotated[list[str], add]
