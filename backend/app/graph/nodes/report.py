"""Report node: assemble the final, source-attributed briefing."""

from __future__ import annotations

import json

from langchain_core.messages import HumanMessage, SystemMessage

from app.config import settings
from app.graph import mock, prompts
from app.graph.llm import get_chat
from app.graph.state import (
    ResearchState,  # noqa: TC001 - used as a runtime-cheap annotation
)
from app.graph.util import dedupe_sources
from app.logging_config import get_logger
from app.schemas.report import ResearchReport, Source

logger = get_logger("app.graph.report")


async def report_node(state: ResearchState) -> dict:
    company = state["company_name"]
    objective = state["objective"]
    analysis = state.get("analysis") or {}
    sources = dedupe_sources(state.get("sources", []))

    try:
        if settings.mock_mode:
            report = mock.mock_report(company, objective, analysis, sources)
        else:
            llm = get_chat().with_structured_output(ResearchReport)
            report = await llm.ainvoke(
                [
                    SystemMessage(content=prompts.REPORT_SYSTEM),
                    HumanMessage(
                        content=prompts.REPORT_USER.format(
                            company_name=company,
                            objective=objective,
                            analysis=json.dumps(analysis, indent=2),
                        ),
                    ),
                ],
            )
            # Sources are authoritative from research — never trust model-invented ones.
            report.sources = [Source(**s) for s in sources]
            if not report.unknowns:
                report.unknowns = analysis.get("unknowns", [])
        return {"report": report.model_dump()}
    except Exception as exc:  # noqa: BLE001
        logger.warning("report failed, using fallback", extra={"error": str(exc)})
        fallback = mock.mock_report(company, objective, analysis, sources)
        return {"report": fallback.model_dump(), "errors": [f"report error: {exc}"]}
