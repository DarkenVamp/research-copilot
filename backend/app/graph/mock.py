"""Deterministic mock outputs used when no OpenAI key is configured.

This keeps the entire graph — including the conditional retry loop — runnable and
testable with zero external dependencies. The first quality check intentionally
fails so the research→analysis→quality loop is exercised at least once.
"""

from __future__ import annotations

from app.schemas.report import (
    Analysis,
    QualityAssessment,
    ResearchPlan,
    ResearchReport,
    Source,
)


def mock_plan(company: str, website: str | None, objective: str) -> ResearchPlan:
    return ResearchPlan(
        focus_areas=[
            "Company overview and positioning",
            "Products and services",
            "Target customers and segments",
            "Recent business signals",
            "Risks and challenges",
        ],
        search_queries=[
            f"{company} company overview",
            f"{company} products and services",
            f"{company} customers case studies",
            f"{company} funding news hiring",
        ],
        rationale=(
            f"To support the objective '{objective}', the plan gathers grounding on "
            f"what {company} does, who it sells to, and where it is heading."
        ),
    )


def mock_analysis(company: str, objective: str, findings: list[dict]) -> Analysis:
    n = len(findings)
    return Analysis(
        company_overview=(
            f"{company} is a company researched against the objective '{objective}'. "
            f"This analysis is derived from {n} mock research findings."
        ),
        products_and_services=[
            f"{company} core product line",
            f"{company} professional/support services",
        ],
        target_customers=["Mid-market businesses", "Enterprise teams"],
        business_signals=[
            "Active hiring across go-to-market roles",
            "Recent product launch activity",
        ],
        risks_and_challenges=[
            "Competitive market pressure",
            "Execution risk while scaling",
        ],
        unknowns=[
            "Exact revenue figures (not public)",
            "Current vendor relationships",
        ],
    )


def mock_quality(retries: int, threshold: float) -> QualityAssessment:
    # Fail on the first pass to demonstrate conditional routing, then pass.
    if retries < 1:
        return QualityAssessment(
            score=round(threshold - 0.2, 2),
            passed=False,
            issues=["Findings are thin; needs more grounding on customers and signals."],
            gaps_to_research=[
                "customer testimonials",
                "recent funding or revenue",
            ],
        )
    return QualityAssessment(
        score=round(min(threshold + 0.2, 1.0), 2),
        passed=True,
        issues=[],
        gaps_to_research=[],
    )


def mock_report(
    company: str, objective: str, analysis: dict, sources: list[dict]
) -> ResearchReport:
    return ResearchReport(
        company_overview=analysis.get("company_overview", ""),
        products_and_services=analysis.get("products_and_services", []),
        target_customers=analysis.get("target_customers", []),
        business_signals=analysis.get("business_signals", []),
        risks_and_challenges=analysis.get("risks_and_challenges", []),
        discovery_questions=[
            f"What are {company}'s top priorities this year relative to {objective}?",
            "Which teams own this initiative and what does success look like?",
            "What does the current solution landscape look like internally?",
        ],
        outreach_strategy=[
            f"Lead with how you help with {objective}.",
            "Reference a relevant business signal to show you did your homework.",
            "Offer a concrete, low-friction next step (short working session).",
        ],
        unknowns=analysis.get("unknowns", []),
        sources=[Source(**s) for s in sources] if sources else [],
    )
