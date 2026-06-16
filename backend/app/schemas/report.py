"""Structured-output schemas for the LangGraph workflow.

These Pydantic models are reused two ways: as the schema the LLM is forced to
fill (`with_structured_output`) and as the validated shape stored/served by the
API. One definition keeps the graph, the database, and the frontend in sync.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class Source(BaseModel):
    title: str = Field(description="Human-readable title of the source")
    url: str = Field(description="URL of the source")


class ResearchPlan(BaseModel):
    """Planner node output: how the research will be approached."""

    focus_areas: list[str] = Field(
        description="The 3-6 themes worth investigating for this objective"
    )
    search_queries: list[str] = Field(
        description="Concrete web-search queries to run to gather evidence"
    )
    rationale: str = Field(description="Why this plan fits the stated objective")


class Analysis(BaseModel):
    """Analysis node output: structured findings before final report assembly."""

    company_overview: str = Field(description="What the company is and does")
    products_and_services: list[str] = Field(default_factory=list)
    target_customers: list[str] = Field(default_factory=list)
    business_signals: list[str] = Field(
        default_factory=list,
        description="Hiring, funding, launches, partnerships, growth signals",
    )
    risks_and_challenges: list[str] = Field(default_factory=list)
    unknowns: list[str] = Field(
        default_factory=list, description="Important things that could not be confirmed"
    )


class QualityAssessment(BaseModel):
    """Quality-check node output: drives the conditional retry loop."""

    score: float = Field(description="Overall quality 0.0-1.0", ge=0.0, le=1.0)
    passed: bool = Field(description="Whether the analysis is good enough to finalize")
    issues: list[str] = Field(
        default_factory=list, description="Concrete weaknesses found"
    )
    gaps_to_research: list[str] = Field(
        default_factory=list,
        description="Follow-up search queries that would close the biggest gaps",
    )


class ResearchReport(BaseModel):
    """The final briefing returned to the user (all required sections)."""

    company_overview: str = ""
    products_and_services: list[str] = Field(default_factory=list)
    target_customers: list[str] = Field(default_factory=list)
    business_signals: list[str] = Field(default_factory=list)
    risks_and_challenges: list[str] = Field(default_factory=list)
    discovery_questions: list[str] = Field(
        default_factory=list, description="Questions to ask in the meeting"
    )
    outreach_strategy: list[str] = Field(
        default_factory=list, description="Recommended outreach approach as steps"
    )
    unknowns: list[str] = Field(default_factory=list)
    sources: list[Source] = Field(default_factory=list)
