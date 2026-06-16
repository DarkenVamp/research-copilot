"""Research node: gather evidence via web search + website fetch.

Runs twice in the worst case: the first pass works the planner's queries (plus the
company website); subsequent passes are triggered by the quality check and target
only the identified gaps. Per-query failures are caught so one bad search never
sinks the run (failure handling + graceful degradation).
"""

from __future__ import annotations

from app.graph.state import ResearchState
from app.graph.tools import fetch_url, web_search
from app.logging_config import get_logger

logger = get_logger("app.graph.research")


async def research_node(state: ResearchState) -> dict:
    plan = state.get("plan") or {}
    quality = state.get("quality")
    retries = state.get("retries", 0)

    is_followup = bool(quality) and not quality.get("passed", False)
    if is_followup:
        queries = quality.get("gaps_to_research") or plan.get("search_queries", [])
        new_retries = retries + 1
    else:
        queries = plan.get("search_queries", [])
        new_retries = retries

    findings: list[dict] = []
    sources: list[dict] = []
    errors: list[str] = []

    # Only fetch the company website on the first pass.
    if not is_followup:
        website = state.get("website")
        text = await fetch_url(website)
        if text:
            findings.append(
                {
                    "query": "company website",
                    "results": [
                        {"title": "Company website", "url": website, "content": text}
                    ],
                }
            )
            sources.append({"title": "Company website", "url": website})

    for query in queries:
        try:
            results = await web_search(query)
            findings.append({"query": query, "results": results})
            for r in results:
                if r.get("url"):
                    sources.append({"title": r.get("title", ""), "url": r["url"]})
        except Exception as exc:  # noqa: BLE001 - degrade, keep going
            logger.warning(
                "search failed", extra={"ctx_query": query, "ctx_error": str(exc)}
            )
            errors.append(f"search failed for '{query}': {exc}")

    return {
        "findings": findings,
        "sources": sources,
        "errors": errors,
        "retries": new_retries,
    }
